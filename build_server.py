"""Temporary loopback-only file exchange for the disposable build VM."""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--share", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *positional, **kwargs):
            super().__init__(*positional, directory=str(args.share), **kwargs)

        def do_PUT(self):
            names = {"cachyos-codex-260809.iso", "build-receipt.json",
                     "init-config.txt", "init-lts-config.txt", "boot-report.txt"}
            name = self.path.removeprefix("/")
            length = int(self.headers.get("Content-Length", "-1"))
            if name not in names or not 0 <= length <= 5 * 1024**3:
                self.send_error(400)
                return
            destination = args.output / name
            if destination.exists():
                self.send_error(409, "Output already exists")
                return
            temporary = destination.with_suffix(destination.suffix + ".partial")
            with temporary.open("xb") as stream:
                remaining = length
                while remaining:
                    chunk = self.rfile.read(min(1024**2, remaining))
                    if not chunk:
                        raise ConnectionError("Incomplete VM upload")
                    stream.write(chunk)
                    remaining -= len(chunk)
            temporary.rename(destination)
            self.send_response(201)
            self.end_headers()
            self.wfile.write(b"Saved\n")

    ThreadingHTTPServer(("127.0.0.1", 55323), Handler).serve_forever()


if __name__ == "__main__":
    main()
