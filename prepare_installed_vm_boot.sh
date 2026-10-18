#!/usr/bin/bash
# Diagnostics only on the task-owned disposable QEMU disk, never on hardware.
set -euo pipefail
test "$(cat /sys/class/dmi/id/sys_vendor)" = QEMU
test "$(lsblk -dn -o SERIAL /dev/vda)" = CODEX-SMOKE-ONLY
test "$(cat /tmp/native-install-test.exit)" = 0
test ! -f /run/codex-cachyos/credentials.json
test ! -f /run/codex-cachyos/installer.json
target=/run/codex-vm-target
mkdir -p "$target"
mount -o subvol=@ /dev/vda2 "$target"
trap 'umount "$target/boot/efi" 2>/dev/null || true; umount "$target" 2>/dev/null || true' EXIT
mount /dev/vda1 "$target/boot/efi"
python - <<'PY'
import json, stat
from pathlib import Path
target=Path('/run/codex-vm-target')
state=target/'var/lib/codex-cachyos'
assert json.loads((state/'installed.json').read_text())['payload_installed']
assert json.loads((state/'approved-install-plan.json').read_text())['target']['serial']=='CODEX-SMOKE-ONLY'
assert not (state/'codex/auth.json').exists()
assert not (target/'etc/codex-cachyos/live').exists()
assert stat.S_IMODE((target/'etc').stat().st_mode)==0o755
assert (target/'etc/systemd/system/timers.target.wants/codex-cachyos.timer').is_symlink()
grub=target/'etc/default/grub'
original=grub.read_text()
backup=grub.with_name('grub.codex-vm-test-original')
if not backup.exists():
    backup.write_text(original)
extra='noapic console=ttyS0 systemd.mask=display-manager.service systemd.mask=serial-getty@ttyS0.service systemd.debug_shell=ttyS0'
grub.write_text(original+'\n# Private QEMU test diagnostics only.\nGRUB_CMDLINE_LINUX_DEFAULT="${GRUB_CMDLINE_LINUX_DEFAULT} '+extra+'"\n')
PY
arch-chroot "$target" /usr/local/bin/codex --version
arch-chroot "$target" runuser -u codextest -- /usr/local/bin/codex --version
arch-chroot "$target" grub-mkconfig -o /boot/grub/grub.cfg >/tmp/installed-grub-test.log 2>&1
sync
printf 'INSTALLED_PAYLOAD_AND_BOOT_PREPARATION_PASSED\n'
