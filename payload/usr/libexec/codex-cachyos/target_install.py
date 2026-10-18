"""Install the audited payload into the explicitly selected installed root."""
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path

PAYLOAD = Path("/opt/codex-cachyos/payload.tar")


def _timer_link(target):
    return target / "etc/systemd/system/timers.target.wants/codex-cachyos.timer"


def _rollback_payload(target, state):
    if state.get("timer_changed"):
        subprocess.run(["systemctl", "--root", str(target), "disable", "codex-cachyos.timer"],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not state.get("timer_preexisting"):
            _timer_link(target).unlink(missing_ok=True)
    for path in reversed(state.get("copied_paths", [])):
        path.unlink(missing_ok=True)
    marker = state.get("marker")
    if marker is not None and state.get("marker_created"):
        marker.unlink(missing_ok=True)
    approved_plan = state.get("approved_plan")
    if approved_plan is not None and state.get("approved_plan_created"):
        approved_plan.unlink(missing_ok=True)


def _install_payload(target):
    target = Path(target).resolve()
    if target == Path("/") or not (target / "etc/os-release").is_file():
        raise ValueError("Target must be a separately mounted installed operating system")
    if "ID=cachyos" not in (target / "etc/os-release").read_text():
        raise ValueError("Installed target does not identify as CachyOS")
    state = {"timer_changed": False, "timer_preexisting": False,
             "copied_paths": [], "marker": None, "marker_created": False}
    previous_umask = os.umask(0o022)
    try:
        with tarfile.open(PAYLOAD) as archive:
            archive.extractall(target, filter="data")
    finally:
        os.umask(previous_umask)
    try:
        for relative in ("var/lib/codex-cachyos", "var/log/codex-cachyos"):
            directory = target / relative
            directory.mkdir(parents=True, exist_ok=True)
            directory.chmod(0o700)
        timer_link = _timer_link(target)
        state["timer_preexisting"] = timer_link.exists() or timer_link.is_symlink()
        state["timer_changed"] = True
        subprocess.run(["systemctl", "--root", str(target), "enable", "codex-cachyos.timer"], check=True)
        # This session's login is copied only into the user's installed system.
        # It is never part of payload.tar or the distributable ISO.
        auth_transferred = False
        destination = target / "var/lib/codex-cachyos/codex"
        if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
            raise ValueError("Target Codex state path is not a directory")
        destination.mkdir(mode=0o700, parents=True, exist_ok=True)
        destination.chmod(0o700)
        for name in ("config.toml", "auth.json"):
            source = Path("/var/lib/codex-cachyos/codex") / name
            if source.is_file() and not source.is_symlink():
                copied = destination / name
                if copied.exists() or copied.is_symlink():
                    raise ValueError(f"Target Codex state already contains {name}")
                state["copied_paths"].append(copied)
                shutil.copyfile(source, copied)
                copied.chmod(0o600)
                auth_transferred |= name == "auth.json"
        marker = target / "var/lib/codex-cachyos/installed.json"
        if marker.exists() or marker.is_symlink():
            raise ValueError("Target Codex installation marker already exists")
        state["marker"] = marker
        state["marker_created"] = True
        marker.write_text(json.dumps({"payload_installed": True, "oauth_bundled": False,
                                      "live_session_auth_transferred": auth_transferred,
                                      "maintenance_requires_login": True}) + "\n")
        marker.chmod(0o600)
        return state
    except BaseException:
        _rollback_payload(target, state)
        raise


def install_payload(target):
    _install_payload(target)


def _revalidate_current_plan(plan):
    from install_control import disk_inventory, validate_plan

    return validate_plan(plan, disk_inventory(), uefi=Path("/sys/firmware/efi").exists())


def finish_install(plan, password):
    _revalidate_current_plan(plan)
    result = subprocess.run(["lsblk", "--tree", "--json", "--paths", "--output", "PATH,FSTYPE",
                             plan["target"]["path"]], check=True, capture_output=True, text=True)
    partitions = json.loads(result.stdout)["blockdevices"][0].get("children", [])
    roots = [part["path"] for part in partitions if part.get("fstype") == plan["filesystem"]]
    if len(roots) != 1:
        raise RuntimeError("Cannot uniquely identify the installed root; no guessed mount performed")
    target = Path("/run/codex-cachyos/target")
    target.mkdir(parents=True, exist_ok=True)
    command = ["mount"]
    if plan["filesystem"] == "btrfs":
        command += ["-o", "subvol=@"]
    subprocess.run(command + [roots[0], str(target)], check=True)
    state = None
    completed = False
    try:
        state = _install_payload(target)
        subprocess.run(["arch-chroot", str(target), "chpasswd"],
                       input=f'{plan["username"]}:{password}\n', text=True,
                       check=True, capture_output=True)
        # Root administration uses sudo and systemd, not an exposed root password.
        subprocess.run(["arch-chroot", str(target), "passwd", "--lock", "root"],
                       check=True, capture_output=True)
        if not (target / "usr/local/bin/codex-cachyos").is_file():
            raise RuntimeError("Post-install payload verification failed")
        approved_plan = target / "var/lib/codex-cachyos/approved-install-plan.json"
        if approved_plan.exists() or approved_plan.is_symlink():
            raise ValueError("Target approved installation plan already exists")
        state["approved_plan"] = approved_plan
        state["approved_plan_created"] = True
        approved_plan.write_text(
            json.dumps(plan, indent=2) + "\n")
        os.chmod(approved_plan, 0o600)
        completed = True
    except BaseException:
        if state is not None:
            _rollback_payload(target, state)
        raise
    finally:
        try:
            subprocess.run(["umount", str(target)], check=True)
        except BaseException:
            if completed and state is not None:
                _rollback_payload(target, state)
            raise
