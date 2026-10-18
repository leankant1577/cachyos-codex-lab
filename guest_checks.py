"""Non-inference integration checks inside the isolated Linux build guest."""
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path


def main():
    control = Path("/usr/libexec/codex-cachyos/target_install.py")
    specification = importlib.util.spec_from_file_location("target_install", control)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix="codex-target-test-", dir="/tmp") as temporary:
        target = Path(temporary)
        (target / "etc").mkdir()
        (target / "etc/os-release").write_text("ID=cachyos\nNAME=CachyOS\n")
        base_units = target / "usr/lib/systemd/system"
        base_units.mkdir(parents=True)
        shutil.copyfile("/usr/lib/systemd/system/timers.target", base_units / "timers.target")
        os.umask(0o077)
        module.install_payload(target)
        for relative in ("usr/libexec/codex-cachyos", "usr/share/codex-cachyos", "opt/openai-codex"):
            assert stat.S_IMODE((target / relative).stat().st_mode) == 0o755, relative
        assert (target / "etc/systemd/system/timers.target.wants/codex-cachyos.timer").is_symlink()
        assert not (target / "etc/codex-cachyos/live").exists()
        assert not (target / "var/lib/codex-cachyos/codex/auth.json").exists()
        for relative in ("var/lib/codex-cachyos", "var/log/codex-cachyos"):
            assert stat.S_IMODE((target / relative).stat().st_mode) == 0o700
        for relative in ("usr/local/bin/codex", "usr/local/bin/codex-cachyos"):
            assert os.access(target / relative, os.X_OK)
        package = target / "opt/openai-codex/0.163.0/bin/codex"
        version = subprocess.check_output([str(package), "--version"], text=True).strip()
        assert version == "codex-cli 0.163.0", version
        units = target / "usr/lib/systemd/system"
        subprocess.run(["systemd-analyze", "verify", *map(str, units.glob("codex-cachyos.*")),
                        str(units / "codex-cachyos-live.service")], check=True)
        print(json.dumps({"target_payload_extraction": "passed", "timer_enable": "passed",
                          "private_directory_modes": "passed", "no_auth_in_target": True,
                          "no_live_marker_in_target": True, "unit_validation": "passed",
                          "target_codex_version": version, "native_install_executed": False,
                          "oauth_or_inference_executed": False}, indent=2))


if __name__ == "__main__":
    main()
