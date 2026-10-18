import gzip
import stat
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def parse_newc(data):
    entries = {}
    pos = 0
    while True:
        assert data[pos:pos + 6] == b"070701"
        fields = [int(data[pos + 6 + n * 8:pos + 14 + n * 8], 16) for n in range(13)]
        pos += 110
        name = data[pos:pos + fields[11] - 1].decode()
        pos = (pos + fields[11] + 3) & ~3
        content = data[pos:pos + fields[6]]
        pos = (pos + fields[6] + 3) & ~3
        if name == "TRAILER!!!":
            return entries
        entries[name] = (fields[1], content)


def test_addon_keeps_existing_hooks_and_adds_only_one_executable_late_hook():
    from boot_addon import make_addon
    config = 'HOOKS="udev archiso"\nLATEHOOKS="archiso_pxe_common"\nCLEANUPHOOKS="udev"\n'
    entries = parse_newc(gzip.decompress(make_addon(config)))
    assert entries["config"][1].decode() == config.replace(
        'LATEHOOKS="archiso_pxe_common"',
        'LATEHOOKS="archiso_pxe_common codex_cachyos"')
    assert set(entries) == {"config", "hooks/codex_cachyos"}
    assert stat.S_IMODE(entries["hooks/codex_cachyos"][0]) == 0o755
    hook = entries["hooks/codex_cachyos"][1].decode()
    assert "sha256sum -c" in hook
    assert 'tar -xf' in hook
    assert 'run_latehook()' in hook
    assert 'mount -r' in hook


@pytest.mark.parametrize("config", ["", 'HOOKS="udev"\n', 'LATEHOOKS="one"\nLATEHOOKS="two"\n'])
def test_addon_rejects_unrecognized_initramfs_layout(config):
    from boot_addon import make_addon
    with pytest.raises(ValueError):
        make_addon(config)


def test_addon_rejects_duplicate_installation():
    from boot_addon import make_addon
    with pytest.raises(ValueError):
        make_addon('HOOKS="udev"\nLATEHOOKS="codex_cachyos"\n')
