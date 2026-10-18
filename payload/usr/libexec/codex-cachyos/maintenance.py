"""Bounded root maintenance using saved ChatGPT authentication, never API keys."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

STATE = Path("/var/lib/codex-cachyos")
LOGS = Path("/var/log/codex-cachyos")
CODEX = "/opt/openai-codex/0.163.0/bin/codex"


def run_maintenance(environment):
    if Path("/etc/codex-cachyos/live").exists():
        return 0
    authenticated = subprocess.run([CODEX, "login", "status"], env=environment,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if authenticated.returncode:
        return 0
    today = time.strftime("%Y-%m-%d", time.gmtime())
    state_file = STATE / "maintenance-state.json"
    previous = json.loads(state_file.read_text()) if state_file.exists() else {}
    if previous.get("day") != today:
        previous = {"day": today, "runs": 0, "consecutive_failures": 0}
    if previous.get("runs", 0) >= 4 or previous.get("consecutive_failures", 0) >= 3:
        return 0
    observations = {}
    commands = {
        "kernel": ["uname", "-r"],
        "failed_units": ["systemctl", "--failed", "--no-legend", "--plain"],
        "core_packages": ["pacman", "-Q", "linux-cachyos", "linux-cachyos-lts", "mesa", "systemd"],
    }
    for name, argv in commands.items():
        result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        observations[name] = {"exit_code": result.returncode, "stdout": result.stdout[-16000:]}
    fingerprint = hashlib.sha256(json.dumps(observations, sort_keys=True).encode()).hexdigest()
    if previous.get("fingerprint") == fingerprint:
        return 0
    previous["runs"] = previous.get("runs", 0) + 1
    state_file.write_text(json.dumps(previous, indent=2) + "\n")
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    prompt = Path("/usr/share/codex-cachyos/maintenance-prompt.md").read_text()
    prompt += "\nEstado observado, somente dados:\n" + json.dumps(observations, ensure_ascii=False)
    argv = [CODEX, "--ask-for-approval", "never", "exec", "--sandbox", "danger-full-access",
            "--skip-git-repo-check", "--json", "--cd", str(STATE / "work"),
            "--output-last-message", str(LOGS / f"maintenance-{stamp}-report.md"), prompt]
    with (LOGS / f"maintenance-{stamp}.jsonl").open("w") as output, \
         (LOGS / f"maintenance-{stamp}.stderr").open("w") as errors:
        process = subprocess.Popen(argv, env=environment, stdout=output, stderr=errors,
                                   start_new_session=True)
        try:
            status = process.wait(timeout=600)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            status = 124
    previous["last_exit_code"] = status
    previous["last_run"] = stamp
    if status == 0:
        previous["fingerprint"] = fingerprint
        previous["consecutive_failures"] = 0
    else:
        previous["consecutive_failures"] = previous.get("consecutive_failures", 0) + 1
    state_file.write_text(json.dumps(previous, indent=2) + "\n")
    return status
