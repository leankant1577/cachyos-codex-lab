import copy
import sys
from pathlib import Path

import pytest


CONTROL_DIR = Path(__file__).resolve().parents[1] / "payload" / "usr" / "libexec" / "codex-cachyos"
sys.path.insert(0, str(CONTROL_DIR))

from install_control import plan_digest, validate_plan


def test_inventory_requests_tree_for_partition_mount_checks(monkeypatch):
    import install_control
    from types import SimpleNamespace

    def run(argv, **kwargs):
        assert "--tree" in argv, "PATH without NAME must explicitly request children"
        return SimpleNamespace(stdout='{"blockdevices": []}')

    monkeypatch.setattr(install_control.subprocess, "run", run)
    assert install_control.disk_inventory() == []


PLAN = {
    "schema": 1,
    "target": {
        "path": "/dev/vda",
        "model": "VIRTUAL_DISK",
        "serial": "TEST-ONLY",
        "size_bytes": 68719476736,
    },
    "mode": "erase-whole-disk",
    "preserve_data": False,
    "encrypt_root": False,
    "locale": "pt_BR.UTF-8",
    "keymap": "br",
    "timezone": "America/Sao_Paulo",
    "username": "leand",
    "hostname": "cachyos",
    "desktop": "kde",
    "filesystem": "btrfs",
    "bootloader": "grub",
}

INVENTORY = [
    {
        "path": "/dev/vda",
        "type": "disk",
        "model": "VIRTUAL_DISK",
        "serial": "TEST-ONLY",
        "size": 68719476736,
        "rm": False,
        "mountpoints": [None],
        "children": [],
    }
]


def plan_copy():
    return copy.deepcopy(PLAN)


def inventory_copy():
    return copy.deepcopy(INVENTORY)


def test_valid_plan_enables_headless_whole_disk_install_without_credentials():
    result = validate_plan(plan_copy(), inventory_copy())

    assert result["headless_mode"] is True
    assert result["allow_auto_partition"] is True
    assert result["device"] == "/dev/vda"
    assert "user_pass" not in result
    assert "root_pass" not in result


@pytest.mark.parametrize(
    ("field", "value"),
    [("serial", "OTHER-SERIAL"), ("size_bytes", 68719476735)],
)
def test_target_identity_mismatch_is_rejected(field, value):
    plan = plan_copy()
    plan["target"][field] = value

    with pytest.raises(ValueError, match="target|serial|size|identity"):
        validate_plan(plan, inventory_copy())


def test_mounted_target_is_rejected():
    inventory = inventory_copy()
    inventory[0]["children"] = [
        {"path": "/dev/vda1", "type": "part", "mountpoints": ["/mnt"]}
    ]

    with pytest.raises(ValueError, match="mount|mounted|montad"):
        validate_plan(plan_copy(), inventory)


def test_removable_target_is_rejected():
    inventory = inventory_copy()
    inventory[0]["rm"] = True

    with pytest.raises(ValueError, match="remov|usb|removível"):
        validate_plan(plan_copy(), inventory)


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("preserve_data", "preserv"),
        ("encrypt_root", "encrypt"),
    ],
)
def test_unsupported_preservation_or_encryption_blocks_without_erase_fallback(field, message):
    plan = plan_copy()
    plan[field] = True

    with pytest.raises(ValueError, match=message):
        validate_plan(plan, inventory_copy())

    assert plan["mode"] == "erase-whole-disk"


@pytest.mark.parametrize(
    "field,value",
    [
        ("username", "leand;touch /tmp/pwned"),
        ("hostname", "cachyos$(id)"),
    ],
)
def test_identity_fields_reject_shell_metacharacters(field, value):
    plan = plan_copy()
    plan[field] = value

    with pytest.raises(ValueError, match="username|hostname|character|shell"):
        validate_plan(plan, inventory_copy())


def test_unknown_plan_key_is_rejected():
    plan = plan_copy()
    plan["unexpected"] = True

    with pytest.raises(ValueError, match="unknown|unexpected|schema|field|chave"):
        validate_plan(plan, inventory_copy())


@pytest.mark.parametrize("field", ["user_pass", "root_pass"])
def test_credentials_are_rejected_from_plan(field):
    plan = plan_copy()
    plan[field] = "must-not-be-in-json"

    with pytest.raises(ValueError, match="credential|password|senha|pass"):
        validate_plan(plan, inventory_copy())


def test_plan_digest_is_independent_of_key_order():
    reordered = {key: PLAN[key] for key in reversed(list(PLAN))}
    reordered["target"] = {
        key: PLAN["target"][key] for key in reversed(list(PLAN["target"]))
    }

    assert plan_digest(PLAN) == plan_digest(reordered)


def test_plan_digest_changes_when_destination_changes():
    changed = plan_copy()
    changed["target"]["path"] = "/dev/vdb"

    assert plan_digest(PLAN) != plan_digest(changed)
