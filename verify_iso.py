"""Compare the delivered ISO with its receipt and unchanged official SquashFS."""
import argparse
import hashlib
import json
from pathlib import Path

import pycdlib


def image_file_hash(image, path):
    digest = hashlib.sha256()
    with image.open_file_from_iso(rr_path=path) as source:
        while block := source.read(4 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--iso", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text())
    with args.iso.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    assert digest == receipt["iso_sha256"], "Delivered image differs from build receipt"
    assert args.iso.stat().st_size == receipt["iso_bytes"]
    hashes = []
    for path in (args.original, args.iso):
        image = pycdlib.PyCdlib()
        image.open(str(path))
        try:
            hashes.append(image_file_hash(image, "/arch/x86_64/airootfs.sfs"))
            if path == args.iso:
                assert image_file_hash(image, "/codex/payload.tar") == receipt["payload_sha256"]
        finally:
            image.close()
    assert hashes[0] == hashes[1], "Official SquashFS changed"
    print(json.dumps({"iso_sha256": digest, "receipt_matches": True,
                      "payload_checksum_matches": True,
                      "original_squashfs_unchanged": True,
                      "squashfs_sha256": hashes[0]}, indent=2))


if __name__ == "__main__":
    main()
