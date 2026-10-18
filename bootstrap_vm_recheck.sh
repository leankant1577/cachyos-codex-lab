#!/usr/bin/bash
# Reuse only the two task-owned virtual disks, without formatting either here.
set -euo pipefail
test "$(lsblk -dn -o SERIAL /dev/vda)" = CODEX-SMOKE-ONLY
test "$(lsblk -dn -o SERIAL /dev/vdb)" = CODEX-BUILD-ONLY
mkdir -p /mnt/work /mnt/old-root
mountpoint -q /mnt/work || mount /dev/vdb /mnt/work
if mountpoint -q /mnt/old-root; then umount /mnt/old-root; fi
mount -o subvolid=5 /dev/vda2 /mnt/old-root
mkdir -p /mnt/work/pkg-cache
cp -a /mnt/old-root/@cache/codex-test-cache/. /mnt/work/pkg-cache/
umount /mnt/old-root
mount --bind /mnt/work/pkg-cache /var/cache/pacman/pkg
curl --fail --silent --show-error http://10.0.2.2:55323/guest-checks.sh -o /tmp/guest-checks.sh
set +e
bash /tmp/guest-checks.sh >/mnt/work/permissions-before.log 2>&1
before=$?
set -e
test "$before" -ne 0
printf 'OLD_PERMISSION_REGRESSION_REPRODUCED=%s\n' "$before"
pacman -Sy --needed --noconfirm libisoburn >/mnt/work/xorriso-recheck-install.log 2>&1
mkdir -p /tmp/initrd/usr/bin
ln -sf /usr/lib/initcpio/busybox /tmp/initrd/usr/bin/busybox
mkdir -p /mnt/work/inputs
curl --fail --silent --show-error http://10.0.2.2:55323/payload.tar -o /mnt/work/inputs/payload.tar
curl --fail --silent --show-error http://10.0.2.2:55323/payload.sha256 -o /mnt/work/inputs/payload.sha256
(cd /mnt/work/inputs && sha256sum -c payload.sha256 && /usr/lib/initcpio/busybox sha256sum -c payload.sha256)
tar -xf /mnt/work/inputs/payload.tar -C /
cp /mnt/work/inputs/payload.tar /opt/codex-cachyos/payload.tar
bash /tmp/guest-checks.sh >/mnt/work/permissions-after.log 2>&1
printf 'UPDATED_PERMISSION_REGRESSION_PASSED\n'
mv /mnt/work/cachyos-codex-260809.iso /mnt/work/candidate-6.iso
mv /mnt/work/build-receipt.json /mnt/work/build-receipt-candidate-6.json
curl --fail --silent --show-error http://10.0.2.2:55323/remaster-whpx.sh -o /mnt/work/remaster-whpx.sh
nohup bash /mnt/work/remaster-whpx.sh >/mnt/work/remaster-v7.log 2>&1 </dev/null &
printf 'BUILD_PID=%s\n' "$!"
