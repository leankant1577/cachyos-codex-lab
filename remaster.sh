#!/usr/bin/bash
# Run only inside the disposable build VM with the original ISO mounted read-only.
set -euo pipefail
mkdir -p /mnt/work/inputs
cd /mnt/work/inputs
for name in payload.tar payload.sha256 initramfs-linux-cachyos.img initramfs-linux-cachyos-lts.img inputs.json; do
    curl --fail --silent --show-error --output "$name" "http://10.0.2.2:55323/$name"
done
sha256sum -c payload.sha256
/tmp/initrd/usr/bin/busybox sha256sum -c payload.sha256
test ! -e /mnt/work/cachyos-codex-260809.iso
xorriso -indev stdio:/dev/sr0 -outdev /mnt/work/cachyos-codex-260809.iso \
    -boot_image any replay \
    -map payload.tar /codex/payload.tar \
    -map payload.sha256 /codex/payload.sha256 \
    -map inputs.json /codex/inputs.json \
    -map initramfs-linux-cachyos.img /arch/boot/x86_64/initramfs-linux-cachyos.img \
    -map initramfs-linux-cachyos-lts.img /arch/boot/x86_64/initramfs-linux-cachyos-lts.img \
    -volume_date uuid 2026080915470300 \
    -commit -end
python - <<'PY'
import hashlib, json, pathlib, subprocess
output = pathlib.Path('/mnt/work/cachyos-codex-260809.iso')
with output.open('rb') as stream:
    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
report = subprocess.run(['xorriso', '-indev', str(output), '-report_el_torito', 'plain',
                         '-report_system_area', 'plain'], capture_output=True, text=True, check=True)
receipt = json.loads(pathlib.Path('inputs.json').read_text())
receipt.update(iso_sha256=digest, iso_bytes=output.stat().st_size,
               boot_report=report.stdout + report.stderr)
pathlib.Path('/mnt/work/build-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
PY
curl --fail --silent --show-error -T /mnt/work/build-receipt.json http://10.0.2.2:55323/build-receipt.json
curl --fail --silent --show-error -T /mnt/work/cachyos-codex-260809.iso http://10.0.2.2:55323/cachyos-codex-260809.iso
printf '\nBUILD_AND_UPLOAD_FINISHED\n'
