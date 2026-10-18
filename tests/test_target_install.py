"""Installation finalization protects the selected target and rolls back artifacts."""
import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


CONTROL = Path(__file__).resolve().parents[1] / "payload/usr/libexec/codex-cachyos"
SPEC = importlib.util.spec_from_file_location("target_install_under_test", CONTROL / "target_install.py")
target_install = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(target_install)


def _plan():
    return {
        "schema": 1,
        "target": {"path": "/dev/vda", "model": "VIRTUAL_DISK",
                    "serial": "TEST-ONLY", "size_bytes": 68719476736},
        "mode": "erase-whole-disk", "preserve_data": False, "encrypt_root": False,
        "locale": "pt_BR.UTF-8", "keymap": "br", "timezone": "America/Sao_Paulo",
        "username": "leand", "hostname": "cachyos", "desktop": "kde",
        "filesystem": "btrfs", "bootloader": "grub",
    }


def test_finish_revalidates_before_mount(monkeypatch):
    plan = _plan()
    calls = []

    def reject(_plan):
        calls.append("validate")
        raise ValueError("target identity mismatch")

    monkeypatch.setattr(target_install, "_revalidate_current_plan", reject)

    def run(argv, **kwargs):
        calls.append(argv[0])
        pytest.fail("mount or lsblk ran before plan revalidation")

    monkeypatch.setattr(target_install.subprocess, "run", run)
    with pytest.raises(ValueError, match="target identity mismatch"):
        target_install.finish_install(plan, "Synthetic-test-only-2026")
    assert calls == ["validate"]


def test_finish_failure_disables_timer_and_removes_oauth(monkeypatch, tmp_path):
    plan = _plan()
    target = tmp_path / "target"
    target.mkdir()
    auth = target / "var/lib/codex-cachyos/codex/auth.json"
    marker = target / "var/lib/codex-cachyos/installed.json"
    timer = target / "etc/systemd/system/timers.target.wants/codex-cachyos.timer"

    monkeypatch.setattr(target_install, "_revalidate_current_plan", lambda _plan: {})

    def fake_payload(path):
        auth.parent.mkdir(parents=True)
        auth.write_text("test-token")
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("marker")
        timer.parent.mkdir(parents=True, exist_ok=True)
        timer.write_text("timer-link-fixture")
        return {"timer_changed": True, "timer_preexisting": False,
                "copied_paths": [auth], "marker": marker, "marker_created": True}

    monkeypatch.setattr(target_install, "_install_payload", fake_payload)
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        if argv[0] == "lsblk":
            assert "--tree" in argv, "PATH without NAME requires explicit tree output"
            return SimpleNamespace(stdout=json.dumps({"blockdevices": [
                {"children": [{"path": "/dev/vda1", "fstype": "btrfs"}]}
            ]}))
        if argv[0] == "arch-chroot" and argv[-1] == "chpasswd":
            raise subprocess.CalledProcessError(1, argv)
        return SimpleNamespace(stdout="")

    monkeypatch.setattr(target_install.subprocess, "run", run)
    monkeypatch.setattr(target_install, "Path", lambda value: target if value == "/run/codex-cachyos/target" else Path(value))

    with pytest.raises(subprocess.CalledProcessError):
        target_install.finish_install(plan, "Synthetic-test-only-2026")

    assert not auth.exists()
    assert not marker.exists()
    assert not timer.exists()
    assert any(argv[:4] == ["systemctl", "--root", str(target), "disable"] for argv in calls)
    assert any(argv[0] == "umount" for argv in calls)
