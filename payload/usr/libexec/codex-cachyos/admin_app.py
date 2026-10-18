#!/usr/bin/python
"""Root Codex entry point and explicit CachyOS installation controller."""
import argparse
import fcntl
import getpass
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path

from install_control import disk_inventory, plan_digest, validate_plan

STATE = Path("/var/lib/codex-cachyos")
LOGS = Path("/var/log/codex-cachyos")
RUNTIME = Path("/run/codex-cachyos")
SHARE = Path("/usr/share/codex-cachyos")
CODEX = "/opt/openai-codex/0.163.0/bin/codex"


def setup():
    os.umask(0o077)
    for directory in (STATE, LOGS, RUNTIME, STATE / "work", STATE / "codex"):
        directory.mkdir(parents=True, exist_ok=True)
        directory.chmod(0o700)
    shutil.copyfile(SHARE / "AGENTS.md", STATE / "work/AGENTS.md")
    config = STATE / "codex/config.toml"
    if not config.exists():
        config.write_text('forced_login_method = "chatgpt"\ncli_auth_credentials_store = "file"\n'
                          '\n[projects."/var/lib/codex-cachyos/work"]\ntrust_level = "trusted"\n')
    environment = os.environ.copy()
    environment.pop("OPENAI_API_KEY", None)
    environment.pop("CODEX_API_KEY", None)
    environment["CODEX_HOME"] = str(STATE / "codex")
    environment["PATH"] = "/opt/openai-codex/0.163.0/codex-path:" + environment.get("PATH", "")
    return environment


def check_plan(path):
    plan = json.loads(Path(path).read_text())
    native = validate_plan(plan, disk_inventory(), uefi=Path("/sys/firmware/efi").exists())
    zone = Path("/usr/share/zoneinfo") / plan["timezone"]
    if not zone.is_file():
        raise ValueError("timezone: fuso horário não encontrado")
    return plan, native


def collect_credentials(path):
    credential_file = RUNTIME / "credentials.json"
    credential_file.unlink(missing_ok=True)
    plan, _ = check_plan(path)
    terminal = os.ttyname(sys.stdin.fileno()) if sys.stdin.isatty() else ""
    if not terminal.startswith("/dev/tty"):
        # A Codex tool's pipe or pseudoterminal cannot receive the human's
        # password directly. Switch to a local VT, then return to Codex.
        print("Digite a senha no console local que será aberto. Ela não passa pelo chat.", flush=True)
        subprocess.run(["openvt", "--switch", "--wait", "--", "/usr/local/bin/codex-cachyos",
                        "credenciais", str(Path(path).resolve())], check=True)
        if not credential_file.is_file():
            raise ValueError("A senha local não foi confirmada. Execute credenciais novamente.")
        return
    password = getpass.getpass(f'Senha local para {plan["username"]}, não enviar ao chat: ')
    if len(password) < 12 or any(character in password for character in ("\n", "\r", ":")):
        raise ValueError("Use pelo menos 12 caracteres, sem quebra de linha ou dois-pontos")
    if password != getpass.getpass("Repita a senha local: "):
        raise ValueError("As senhas não coincidem")
    (RUNTIME / "credentials.json").write_text(json.dumps(
        {"plan_sha256": plan_digest(plan), "user_password": password}))
    print("Credencial local temporária preparada. Nenhuma senha foi incluída no plano.")


def run_install(path, approved):
    # Never invoke the native installer merely to validate a user-generated plan.
    plan, native = check_plan(path)
    digest = plan_digest(plan)
    if approved != digest:
        raise ValueError("O hash aprovado no chat não corresponde ao plano atual")
    credentials = RUNTIME / "credentials.json"
    if not credentials.is_file():
        raise ValueError("Falta a senha local: execute o helper credenciais no terminal")
    secret = json.loads(credentials.read_text())
    if secret.get("plan_sha256") != digest:
        raise ValueError("A credencial local pertence a outro plano")
    config = RUNTIME / "installer.json"
    run_log = LOGS / f"install-{int(time.time())}.log"
    with (RUNTIME / "install.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            # The upstream installer receives temporary random credentials only.
            # The user's real password is applied through chpasswd stdin afterwards.
            native["user_pass"] = secrets.token_urlsafe(36)
            native["root_pass"] = secrets.token_urlsafe(36)
            config.write_text(json.dumps(native))
            check_plan(path)  # Recheck identity/mounts immediately before starting.
            print(f"Executando o plano aprovado {digest}. Log privado: {run_log}", flush=True)
            with run_log.open("w") as log:
                result = subprocess.run(["cachyos-installer", "--config", str(config)],
                                        stdout=log, stderr=subprocess.STDOUT, umask=0o022)
            if result.returncode:
                raise RuntimeError(f"Instalador retornou {result.returncode}. Não repetir automaticamente; examine {run_log}")
            from target_install import finish_install
            finish_install(plan, secret["user_password"])
            (STATE / "last-install.json").write_text(json.dumps(
                {"plan_sha256": digest, "native_exit_code": result.returncode,
                 "post_install_payload": True, "automatic_reboot": False}) + "\n")
            print("Instalação e payload concluídos. Não houve reinicialização automática.")
        finally:
            config.unlink(missing_ok=True)
            credentials.unlink(missing_ok=True)


def start_agent(environment, maintenance=False):
    status = subprocess.run([CODEX, "login", "status"], env=environment,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if status.returncode:
        result = subprocess.run([CODEX, "login", "--device-auth"], env=environment)
        if result.returncode:
            return result.returncode
    prompt = (SHARE / ("maintenance-prompt.md" if maintenance else "install-prompt.md")).read_text()
    return subprocess.run([CODEX, "--ask-for-approval", "never", "--sandbox",
                           "danger-full-access", "--cd", str(STATE / "work"), prompt],
                          env=environment).returncode


def main():
    if os.geteuid() != 0:
        os.execvp("sudo", ["sudo", "-H", "/usr/local/bin/codex-cachyos", *sys.argv[1:]])
    parser = argparse.ArgumentParser(description="Codex administrador do CachyOS")
    parser.add_argument("action", choices=("iniciar", "admin", "login", "status", "inventario",
                                           "validar-plano", "credenciais", "instalar", "manutencao"))
    parser.add_argument("plan", nargs="?")
    parser.add_argument("--aprovado-sha256")
    args = parser.parse_args()
    environment = setup()
    if args.action in ("iniciar", "admin"):
        return start_agent(environment, maintenance=args.action == "admin")
    if args.action == "login":
        return subprocess.run([CODEX, "login", "--device-auth"], env=environment).returncode
    if args.action == "status":
        return subprocess.run([CODEX, "login", "status"], env=environment).returncode
    if args.action == "inventario":
        print(json.dumps(disk_inventory(), indent=2))
    elif args.action == "manutencao":
        from maintenance import run_maintenance
        return run_maintenance(environment)
    elif not args.plan:
        parser.error("informe o caminho do plano JSON")
    elif args.action == "validar-plano":
        plan, native = check_plan(args.plan)
        print(json.dumps({"valid": True, "plan_sha256": plan_digest(plan), "plan": plan,
                          "native_preview_without_credentials": native}, indent=2))
    elif args.action == "credenciais":
        collect_credentials(args.plan)
    elif args.action == "instalar":
        run_install(args.plan, args.aprovado_sha256)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"Bloqueado: {error}", file=sys.stderr)
        raise SystemExit(1)
