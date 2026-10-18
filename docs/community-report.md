# Experimental CachyOS Codex integration

Repository: https://github.com/leankant1577/cachyos-codex-lab

This independent experiment was built with substantial assistance from Codex.
It adds the official Codex CLI 0.163.0 to a personal CachyOS remaster. The live
session starts a root console agent and calls the existing native installer
0.12.4-bb3eccb-20260804 in headless mode. No installer wizard is involved.

The current executor supports a new UEFI installation on one dedicated internal
disk, KDE/GNOME/XFCE, btrfs/ext4 and GRUB. Disk identity and mounted partitions
are checked. Preserving data, dual boot and encrypted root are blocked rather
than silently replaced by erasing a disk. Human OAuth, a hidden local password
and approval of the concrete erase plan remain necessary.

The installed root service uses saved ChatGPT OAuth, with a daily call limit
and failure pause. No credentials are bundled. Prompts define its intended
scope; they do not restrict root access at the operating system level.

Evidence includes 32 unit tests, a native UEFI/KDE/btrfs installation into a
private QEMU disk, booting that installed disk without ISO media, correct
payload permissions, a verified synthetic user password, a locked root
password, and a timer that skips model execution without authentication.
The original SquashFS remains byte-identical. OAuth conversation, real hardware,
autonomous repair quality and performance improvements have not been validated.

The bugs found during testing were in this integration, not claimed as CachyOS
bugs. The repository contains source, tests and summarized evidence. No ISO or
private installation log has been published externally.

We would welcome guidance on the appropriate community discussion and upstream
contribution path. Before offering a customized ISO for public download, we
would also like clarification on the repository usage policy as it applies
to this personal remaster and any permission needed for public redistribution.
No official endorsement is implied.
