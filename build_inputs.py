"""Create reproducible build inputs from authored files and a pinned official package."""
import argparse
import hashlib
import io
import json
import tarfile
from pathlib import Path, PurePosixPath

import pycdlib

from boot_addon import make_addon

ISO_SHA256 = "959f6577f45e25ee9fd8c220fd221b08e4ea79412c7315c0f922dd6d86d5e33c"
PACKAGE_SHA256 = "582646c6bf0561eb0de540f7fc85b9121b0091a826bc6e96830b7f1722122182"


def sha256(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source_root = Path(__file__).resolve().parent
    share = args.build / "share"
    share.mkdir(parents=True, exist_ok=True)
    package = args.build / "codex-package-linux.tar.gz"
    if sha256(args.original) != ISO_SHA256 or sha256(package) != PACKAGE_SHA256:
        raise ValueError("Input ISO or official Codex package hash mismatch")
    payload = share / "payload.tar"
    with tarfile.open(payload, "w", format=tarfile.PAX_FORMAT) as output:
        for source in sorted((source_root / "payload").rglob("*")):
            if not source.is_file() or "__pycache__" in source.parts or source.suffix == ".pyc":
                continue
            relative = source.relative_to(source_root / "payload").as_posix()
            content = source.read_bytes().replace(b"\r\n", b"\n")
            member = tarfile.TarInfo(relative)
            member.mode = 0o755 if relative.startswith("usr/local/bin/") or source.suffix == ".py" else 0o644
            member.uid = member.gid = 0
            member.mtime = 0
            member.size = len(content)
            output.addfile(member, io.BytesIO(content))
        with tarfile.open(package, "r:gz") as official:
            for member in official:
                path = PurePosixPath(member.name)
                if path.is_absolute() or ".." in path.parts:
                    raise ValueError("Unsafe package member path")
                if not (member.isdir() or member.isfile() or member.issym()):
                    raise ValueError("Unexpected package member type")
                if member.issym() and (PurePosixPath(member.linkname).is_absolute() or ".." in PurePosixPath(member.linkname).parts):
                    raise ValueError("Unexpected package symlink")
                reader = official.extractfile(member) if member.isfile() else None
                member.name = "opt/openai-codex/0.163.0/" + member.name
                member.uid = member.gid = 0
                member.uname = member.gname = "root"
                member.mode &= 0o777
                member.mtime = 0
                output.addfile(member, reader)
    digest = sha256(payload)
    # BusyBox in the initramfs treats CR as part of the filename, unlike GNU.
    (share / "payload.sha256").write_bytes(f"{digest}  payload.tar\n".encode("ascii"))
    image = pycdlib.PyCdlib()
    image.open(str(args.original))
    try:
        for suffix, config_name in (("", "init-config.txt"), ("-lts", "init-lts-config.txt")):
            name = f"initramfs-linux-cachyos{suffix}.img"
            destination = share / name
            image.get_file_from_iso(str(destination), rr_path=f"/arch/boot/x86_64/{name}")
            config = (args.output / config_name).read_text()
            with destination.open("ab") as stream:
                stream.write(make_addon(config))
    finally:
        image.close()
    receipt = {"original_iso_sha256": ISO_SHA256, "codex_version": "0.163.0",
               "official_package_sha256": PACKAGE_SHA256, "payload_sha256": digest,
               "payload_bytes": payload.stat().st_size,
               "no_tokens_in_payload": True, "original_squashfs_recompressed": False,
               "iso_source": "https://wiki.cachyos.org/cachyos_basic/download/",
               "codex_source": "https://github.com/openai/codex/releases/tag/rust-v0.163.0"}
    (share / "inputs.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
