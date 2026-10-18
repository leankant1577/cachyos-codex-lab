"""Run a bounded build command on the task's localhost-only VM console."""
import argparse
import base64
import re
import socket
import sys
import time
import uuid
from pathlib import Path


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path)
    parser.add_argument("--command")
    parser.add_argument("--timeout", type=float, default=50)
    parser.add_argument("--port", type=int, default=55321)
    args = parser.parse_args()
    command = args.file.read_text(encoding="utf-8") if args.file else args.command
    if not command:
        parser.error("provide --file or --command")
    token = uuid.uuid4().hex
    begin = f"BEGIN_{token}"
    end = f"END_{token}"
    encoded = base64.b64encode(command.encode()).decode()
    line = (f"\nprintf '\\n{begin}\\n'; printf '%s' '{encoded}' | "
            f"base64 -d | SYSTEMD_PAGER=cat PAGER=cat bash; printf '\\n{end}:%s\\n' \"$?\"\n")
    received = b""
    deadline = time.monotonic() + args.timeout
    with socket.create_connection(("127.0.0.1", args.port), timeout=5) as connection:
        connection.settimeout(1)
        connection.sendall(line.encode())
        while time.monotonic() < deadline:
            try:
                chunk = connection.recv(65536)
            except socket.timeout:
                continue
            if not chunk:
                break
            received += chunk
            decoded = received.decode(errors="replace").replace("\r", "")
            match = re.search(rf"\n{end}:(\d+)\n", decoded)
            if match:
                start = decoded.find("\n" + begin + "\n")
                print(decoded[start + len(begin) + 2:match.start()].strip())
                return int(match.group(1))
    print(received.decode(errors="replace"), file=sys.stderr)
    print("VM console command did not finish within the time budget", file=sys.stderr)
    return 124


if __name__ == "__main__":
    raise SystemExit(main())
