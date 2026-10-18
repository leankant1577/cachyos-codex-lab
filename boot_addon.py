"""Small additive initramfs overlay, preserving the original SquashFS bytes."""
import gzip
import re

HOOK = r'''#!/usr/bin/ash
run_latehook() {
    local media=/run/archiso/bootmnt
    if [ ! -f "$media/codex/payload.tar" ]; then
        mkdir -p /run/codex-media
        mount -r "$archisodevice" /run/codex-media || return 1
        media=/run/codex-media
    fi
    if ! (cd "$media/codex" && sha256sum -c payload.sha256); then
        err 'Codex payload checksum failed. Integration was not activated.'
        return 1
    fi
    tar -xf "$media/codex/payload.tar" -C /new_root || return 1
    mkdir -p /new_root/opt/codex-cachyos
    cp "$media/codex/payload.tar" /new_root/opt/codex-cachyos/payload.tar || return 1
    chroot /new_root /usr/bin/python /usr/libexec/codex-cachyos/live_setup.py || return 1
    msg 'Codex CachyOS integration ready. No target disk was changed.'
}
'''


def newc(entries):
    output = bytearray()
    for inode, (name, content, mode) in enumerate(
        [*entries, ("TRAILER!!!", b"", 0)], start=1
    ):
        fields = [inode, (0o100000 | mode) if mode else 0, 0, 0, 1, 0,
                  len(content), 0, 0, 0, 0, len(name.encode()) + 1, 0]
        output.extend(b"070701" + "".join(f"{value:08x}" for value in fields).encode())
        output.extend(name.encode() + b"\0")
        output.extend(b"\0" * (-len(output) % 4))
        output.extend(content)
        output.extend(b"\0" * (-len(output) % 4))
    output.extend(b"\0" * (-len(output) % 512))
    return bytes(output)


def make_addon(config):
    matches = list(re.finditer(r'^LATEHOOKS="([^"\n]*)"$', config, re.MULTILINE))
    if len(matches) != 1 or "codex_cachyos" in matches[0].group(1).split():
        raise ValueError("Unknown or already modified initramfs hook configuration")
    old = matches[0]
    hooks = (old.group(1) + " codex_cachyos").strip()
    changed = config[:old.start()] + f'LATEHOOKS="{hooks}"' + config[old.end():]
    archive = newc([("config", changed.encode(), 0o644),
                    ("hooks/codex_cachyos", HOOK.encode(), 0o755)])
    return gzip.compress(archive, mtime=0)
