"""Password input must use a human-accessible local console, never a tool PTY."""
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def app(monkeypatch, tmp_path):
    # fcntl is not available on the Windows build host. No flock operation
    # or installer execution is involved in these input-routing contracts.
    if sys.platform == "win32":
        monkeypatch.setitem(sys.modules, "fcntl", SimpleNamespace(
            LOCK_EX=1, LOCK_NB=4, flock=lambda *args: None))
    control = Path(__file__).resolve().parents[1] / "payload/usr/libexec/codex-cachyos"
    monkeypatch.syspath_prepend(str(control))
    specification = importlib.util.spec_from_file_location("admin_under_test", control / "admin_app.py")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    monkeypatch.setattr(module, "RUNTIME", tmp_path)
    monkeypatch.setattr(module, "check_plan", lambda path: ({"username": "teste"}, {}))
    return module


@pytest.mark.parametrize("terminal", [None, "/dev/pts/7"])
def test_tool_input_routes_to_local_virtual_console(app, monkeypatch, tmp_path, terminal):
    monkeypatch.setattr(app.sys, "stdin", SimpleNamespace(isatty=lambda: terminal is not None,
                                                         fileno=lambda: 0))
    monkeypatch.setattr(app.os, "ttyname", lambda fd: terminal, raising=False)
    calls = []
    def console_child(argv, **kwargs):
        calls.append((argv, kwargs))
        (tmp_path / "credentials.json").write_text("{}")
    monkeypatch.setattr(app.subprocess, "run", console_child)
    monkeypatch.setattr(app.getpass, "getpass", lambda *args: pytest.fail("Secret requested through tool input"))
    app.collect_credentials(tmp_path / "plan.json")
    assert calls == [(["openvt", "--switch", "--wait", "--", "/usr/local/bin/codex-cachyos",
                       "credenciais", str((tmp_path / "plan.json").resolve())], {"check": True})]
    assert (tmp_path / "credentials.json").exists()


def test_cancelled_console_clears_old_secret_and_reports_failure(app, monkeypatch, tmp_path):
    monkeypatch.setattr(app.sys, "stdin", SimpleNamespace(isatty=lambda: False))
    (tmp_path / "credentials.json").write_text("stale test secret")
    monkeypatch.setattr(app.subprocess, "run", lambda *args, **kwargs: None)
    with pytest.raises(ValueError, match="n�o foi confirmada"):
        app.collect_credentials(tmp_path / "plan.json")
    assert not (tmp_path / "credentials.json").exists()


def test_invalid_plan_does_not_retain_previous_password(app, monkeypatch, tmp_path):
    secret = tmp_path / "credentials.json"
    secret.write_text("stale test secret")
    def reject(path):
        raise ValueError("changed disk identity")
    monkeypatch.setattr(app, "check_plan", reject)
    with pytest.raises(ValueError, match="changed disk"):
        app.collect_credentials(tmp_path / "plan.json")
    assert not secret.exists()


def test_physical_console_collects_secret_without_subprocess_arguments(app, monkeypatch, tmp_path):
    monkeypatch.setattr(app.sys, "stdin", SimpleNamespace(isatty=lambda: True, fileno=lambda: 0))
    monkeypatch.setattr(app.os, "ttyname", lambda fd: "/dev/tty2", raising=False)
    monkeypatch.setattr(app.getpass, "getpass", lambda *args: "Synthetic-test-only-2026")
    monkeypatch.setattr(app.subprocess, "run", lambda *args, **kwargs: pytest.fail("Secret passed to subprocess"))
    app.collect_credentials(tmp_path / "plan.json")
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    assert credentials["plan_sha256"] == app.plan_digest({"username": "teste"})
    assert credentials["user_password"] == "Synthetic-test-only-2026"


def test_native_installer_has_public_directory_umask_and_failure_cleans_secrets(app, monkeypatch, tmp_path):
    monkeypatch.setattr(app, "LOGS", tmp_path)
    plan = {"username": "teste"}
    digest = app.plan_digest(plan)
    secret = tmp_path / "credentials.json"
    secret.write_text(json.dumps({"plan_sha256": digest, "user_password": "Synthetic-test-only-2026"}))
    calls = []

    def failed_installer(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(app.subprocess, "run", failed_installer)
    with pytest.raises(RuntimeError, match="Instalador retornou 1"):
        app.run_install(tmp_path / "plan.json", digest)
    assert calls[0][1].get("umask") == 0o022
    assert not secret.exists()
    assert not (tmp_path / "installer.json").exists()
