"""Check the installed private QEMU disk after booting without the live ISO."""
import ctypes
import json
import os
import stat
import subprocess
from pathlib import Path


def output(*args):
    return subprocess.check_output(args, text=True).strip()


def main():
    assert os.geteuid() == 0
    assert Path('/sys/class/dmi/id/sys_vendor').read_text().strip() == 'QEMU'
    assert Path('/sys/firmware/efi').is_dir()
    assert output('lsblk', '-dn', '-o', 'SERIAL', '/dev/vda') == 'CODEX-SMOKE-ONLY'
    assert not Path('/etc/codex-cachyos/live').exists()
    assert 'ID=cachyos' in Path('/etc/os-release').read_text()
    assert output('findmnt', '-n', '-o', 'SOURCE', '/') == '/dev/vda2[/@]'
    assert output('/usr/local/bin/codex', '--version') == 'codex-cli 0.163.0'
    # The normal root entry point initializes private directories after @log mounts.
    status = subprocess.run(['/usr/local/bin/codex-cachyos', 'status'],
                            capture_output=True, text=True)
    assert status.returncode == 1 and 'Not logged in' in status.stdout + status.stderr
    assert output('systemctl', 'is-enabled', 'codex-cachyos.timer') == 'enabled'
    assert output('systemctl', 'is-active', 'codex-cachyos.timer') == 'active'
    assert output('passwd', '-S', 'root').split()[1] == 'L'
    for relative in ('/usr/libexec/codex-cachyos', '/usr/share/codex-cachyos',
                     '/opt/openai-codex'):
        assert stat.S_IMODE(Path(relative).stat().st_mode) == 0o755, relative
    for relative in ('/var/lib/codex-cachyos', '/var/log/codex-cachyos',
                     '/var/lib/codex-cachyos/codex'):
        assert stat.S_IMODE(Path(relative).stat().st_mode) == 0o700, relative
    state = Path('/var/lib/codex-cachyos')
    assert not (state / 'codex/auth.json').exists()
    marker = json.loads((state / 'installed.json').read_text())
    assert marker['payload_installed'] and not marker['live_session_auth_transferred']
    plan = json.loads((state / 'approved-install-plan.json').read_text())
    assert plan['target']['serial'] == 'CODEX-SMOKE-ONLY'
    assert plan['username'] == 'codextest'
    # Verify only the synthetic VM password, without printing its shadow entry.
    shadow = output('getent', 'shadow', 'codextest').split(':')[1]
    library = ctypes.CDLL('libcrypt.so.2')
    library.crypt.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    library.crypt.restype = ctypes.c_char_p
    assert library.crypt(b'codextest12345678', shadow.encode()).decode() == shadow
    subprocess.run(['systemctl', 'start', 'codex-cachyos.service'], check=True)
    assert output('systemctl', 'show', '-p', 'Result', '--value',
                  'codex-cachyos.service') == 'success'
    assert not list(Path('/var/log/codex-cachyos').glob('maintenance-*.jsonl'))
    print(json.dumps({'booted_installed_disk_without_iso': True, 'uefi': True,
                      'codex_version': '0.163.0', 'timer_enabled_and_active': True,
                      'root_password_locked': True, 'synthetic_user_password_verified': True,
                      'payload_permissions': 'passed', 'no_auth_in_installed_system': True,
                      'maintenance_without_auth_skipped_model': True,
                      'oauth_or_inference_executed': False}, indent=2))


if __name__ == '__main__':
    main()
