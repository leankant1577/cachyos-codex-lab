#!/usr/bin/python
"""Configure the live session overlay without modifying the original SquashFS."""
import os
from pathlib import Path


def main():
    os.umask(0o022)
    marker = Path("/etc/codex-cachyos")
    marker.mkdir(parents=True, exist_ok=True)
    (marker / "live").write_text("Codex live integration; no target installation performed.\n")
    autostart = Path("/etc/xdg/autostart")
    autostart.mkdir(parents=True, exist_ok=True)
    for directory in (autostart, Path("/usr/share/autostart")):
        if not directory.exists():
            continue
        for item in directory.glob("*.desktop"):
            if "cachyos-hello" in item.read_text(errors="replace"):
                item.write_text("[Desktop Entry]\nType=Application\nName=CachyOS Hello\nHidden=true\n")
    # Only the live overlay boots into the Codex terminal. The installed
    # system keeps the desktop selected by its owner.
    units = Path("/etc/systemd/system")
    units.mkdir(parents=True, exist_ok=True)
    firstboot = units / "systemd-firstboot.service.d"
    firstboot.mkdir(parents=True, exist_ok=True)
    (firstboot / "10-codex-live.conf").write_text(
        "[Unit]\nConditionPathExists=!/etc/codex-cachyos/live\n")
    default = units / "default.target"
    default.unlink(missing_ok=True)
    default.symlink_to("/usr/lib/systemd/system/multi-user.target")
    wants = units / "multi-user.target.wants"
    wants.mkdir(parents=True, exist_ok=True)
    assistant = wants / "codex-cachyos-live.service"
    assistant.unlink(missing_ok=True)
    assistant.symlink_to("/usr/lib/systemd/system/codex-cachyos-live.service")
    getty = units / "getty@tty1.service"
    getty.unlink(missing_ok=True)
    getty.symlink_to("/dev/null")
    Path("/var/log/codex-cachyos-boot.log").write_text(
        "Payload applied to live overlay. Official headless installer retained.\n"
        "No authentication, AI execution, partitioning or target writes performed by boot hook.\n")


if __name__ == "__main__":
    main()
