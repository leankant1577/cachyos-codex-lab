"""Check the live boot without login, inference or running an installer."""
import json
import os
import subprocess
from pathlib import Path


def output(*argv):
    return subprocess.check_output(argv, text=True).strip()


def main():
    assert os.geteuid() == 0
    assert Path("/sys/class/dmi/id/sys_vendor").read_text().strip() == "QEMU"
    assert Path("/sys/firmware/efi").is_dir()
    assert Path("/etc/codex-cachyos/live").is_file()
    assert output("systemctl", "get-default") == "multi-user.target"
    assert output("systemctl", "is-active", "multi-user.target") == "active"
    assert Path("/etc/systemd/system/multi-user.target.wants/codex-cachyos-live.service").is_symlink()
    assert output("/usr/local/bin/codex", "--version") == "codex-cli 0.163.0"
    status = subprocess.run(["/usr/local/bin/codex-cachyos", "status"], capture_output=True, text=True)
    assert status.returncode == 1, status.stdout + status.stderr
    assert "Not logged in" in status.stderr + status.stdout
    assert not Path("/var/lib/codex-cachyos/codex/auth.json").exists()
    subprocess.run(["systemd-analyze", "verify", "/usr/lib/systemd/system/codex-cachyos-live.service",
                    "/usr/lib/systemd/system/codex-cachyos.service",
                    "/usr/lib/systemd/system/codex-cachyos.timer"], check=True)
    inventory = json.loads(output("/usr/local/bin/codex-cachyos", "inventario"))
    disks = [disk for disk in inventory if disk.get("serial") == "CODEX-SMOKE-ONLY"]
    assert len(disks) == 1, "Only the private VM smoke disk may be used in this test"
    disk = disks[0]
    plan = json.loads(Path("/usr/share/codex-cachyos/plan-template.json").read_text())
    plan["target"] = {"path": disk["path"], "model": disk.get("model") or "",
                      "serial": disk["serial"], "size_bytes": disk["size"]}
    plan.update(username="codextest", hostname="cachyos-test", filesystem="btrfs")
    plan_file = Path("/tmp/codex-smoke-plan.json")
    plan_file.write_text(json.dumps(plan))
    plan_file.chmod(0o600)
    validation = json.loads(output("/usr/local/bin/codex-cachyos", "validar-plano", str(plan_file)))
    assert validation["valid"] and validation["native_preview_without_credentials"]["headless_mode"]
    mounted_partition_rejected = None
    if Path('/dev/vda2').exists():
        temporary_mount = Path('/run/codex-mounted-rejection-test')
        temporary_mount.mkdir(exist_ok=True)
        subprocess.run(['mount', '-o', 'ro,subvol=@', '/dev/vda2', str(temporary_mount)], check=True)
        try:
            rejected = subprocess.run(['/usr/local/bin/codex-cachyos', 'validar-plano', str(plan_file)],
                                      capture_output=True, text=True)
            assert rejected.returncode != 0
            assert 'mounted target' in rejected.stdout + rejected.stderr
            mounted_partition_rejected = True
        finally:
            subprocess.run(['umount', str(temporary_mount)], check=True)
    for directory in ("/var/lib/codex-cachyos", "/var/log/codex-cachyos"):
        assert Path(directory).stat().st_mode & 0o777 == 0o700
    print(json.dumps({"uefi": True, "root": True, "live_payload": "passed",
                      "systemd_default": "multi-user.target", "codex_version": "0.163.0",
                      "unit_validation": "passed", "plan_validation_on_private_vm_disk": "passed",
                      "mounted_partition_rejected": mounted_partition_rejected,
                      "live_codex_service_masked_for_test_only": True,
                      "no_login_or_inference": True, "installer_executed": False}, indent=2))


if __name__ == "__main__":
    main()
