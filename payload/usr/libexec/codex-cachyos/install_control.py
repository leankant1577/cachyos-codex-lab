"""Validate explicit installation plans before invoking CachyOS headless."""
import hashlib
import json
import re
import subprocess

PLAN_FIELDS = {"schema", "target", "mode", "preserve_data", "encrypt_root",
               "locale", "keymap", "timezone", "username", "hostname",
               "desktop", "filesystem", "bootloader"}
TARGET_FIELDS = {"path", "model", "serial", "size_bytes"}


def plan_digest(plan):
    serialized = json.dumps(plan, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(serialized.encode()).hexdigest()


def disk_inventory():
    result = subprocess.run(
        ["lsblk", "--tree", "--json", "--bytes", "--output",
         "PATH,TYPE,SIZE,MODEL,SERIAL,TRAN,RM,MOUNTPOINTS"],
        check=True, capture_output=True, text=True)
    return json.loads(result.stdout)["blockdevices"]


def has_mounts(device):
    return any(device.get("mountpoints") or []) or any(
        has_mounts(child) for child in device.get("children", []))


def validate_plan(plan, inventory, uefi=True):
    if not isinstance(plan, dict):
        raise ValueError("schema: plano deve ser um objeto JSON")
    if any("pass" in field or "secret" in field or "token" in field for field in plan):
        raise ValueError("credentials/password: senhas e tokens nunca pertencem ao plano")
    if set(plan) != PLAN_FIELDS or plan.get("schema") != 1:
        raise ValueError("unknown/missing schema field: confira as chaves do plano")
    if plan["preserve_data"] is not False:
        raise ValueError("preserve_data: fluxo de preserva��o ainda n�o homologado; nenhuma instala��o executada")
    if plan["encrypt_root"] is not False:
        raise ValueError("encrypt_root: criptografia neste fluxo ainda n�o homologada")
    if plan["mode"] != "erase-whole-disk":
        raise ValueError("mode: somente plano expl�cito erase-whole-disk � aceito neste fluxo")
    if not uefi:
        raise ValueError("UEFI: este fluxo de instala��o ainda n�o foi homologado para BIOS legado")
    target = plan["target"]
    if not isinstance(target, dict) or set(target) != TARGET_FIELDS:
        raise ValueError("target identity: modelo, serial, caminho e tamanho s�o obrigat�rios")
    if not isinstance(target["path"], str) or not re.fullmatch(r"/dev/[a-zA-Z0-9_-]+", target["path"]):
        raise ValueError("target path: use o caminho Linux real mostrado pelo invent�rio")
    matches = [disk for disk in inventory if disk.get("path") == target["path"]]
    if len(matches) != 1 or matches[0].get("type") != "disk":
        raise ValueError("target identity: disco inteiro n�o identificado de forma �nica")
    disk = matches[0]
    if not str(target["serial"]).strip():
        raise ValueError("serial: identifica��o ausente, n�o selecionar automaticamente")
    for key in ("model", "serial"):
        if str(disk.get(key) or "").strip() != str(target[key]).strip():
            raise ValueError(f"target identity mismatch: {key}")
    if type(target["size_bytes"]) is not int or disk.get("size") != target["size_bytes"]:
        raise ValueError("target size identity mismatch")
    if disk.get("rm") in (True, 1, "1") or disk.get("tran") == "usb":
        raise ValueError("removable/usb: m�dia remov�vel n�o � alvo deste fluxo")
    if has_mounts(disk):
        raise ValueError("mounted target: desmonte o alvo e revalide; n�o remover montagens automaticamente")
    patterns = {
        "username": r"[a-z_][a-z0-9_-]{0,31}",
        "hostname": r"[a-z0-9][a-z0-9-]{0,62}",
        "locale": r"[a-z]{2}_[A-Z]{2}\.UTF-8",
        "keymap": r"[a-zA-Z0-9_-]{1,32}",
        "timezone": r"[A-Za-z0-9_+-]+(?:/[A-Za-z0-9_+-]+){1,3}",
    }
    for field, pattern in patterns.items():
        if not isinstance(plan[field], str) or not re.fullmatch(pattern, plan[field]):
            raise ValueError(f"{field}: invalid characters")
    if plan["username"] == "root":
        raise ValueError("username: crie um usu�rio pessoal separado de root")
    if plan["desktop"] not in {"kde", "gnome", "xfce"}:
        raise ValueError("desktop: perfil n�o verificado neste fluxo")
    if plan["filesystem"] not in {"btrfs", "ext4"} or plan["bootloader"] != "grub":
        raise ValueError("filesystem/bootloader: combina��o ainda n�o verificada")
    return {
        "install_type": "simple", "headless_mode": True,
        "device": target["path"], "fs_name": plan["filesystem"],
        "allow_auto_partition": True, "partitions": [],
        "subvolumes": "default", "locale": plan["locale"],
        "xkbmap": plan["keymap"], "timezone": plan["timezone"],
        "user_name": plan["username"], "hostname": plan["hostname"],
        "user_shell": "/bin/bash", "desktop": plan["desktop"],
        "kernel": "linux-cachyos linux-cachyos-lts", "bootloader": "grub",
        "autologin": False, "chwd": True,
    }
