"""Send one QMP command to the task's isolated local smoke-test VM."""
import argparse
import json
import socket


def request(stream, command):
    stream.write((json.dumps(command) + "\r\n").encode())
    stream.flush()
    while True:
        response = json.loads(stream.readline())
        if "return" in response or "error" in response:
            return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", help="QMP command as JSON")
    parser.add_argument("--port", type=int, default=55332)
    args = parser.parse_args()
    with socket.create_connection(("127.0.0.1", args.port), timeout=10) as connection:
        stream = connection.makefile("rwb")
        json.loads(stream.readline())
        capabilities = request(stream, {"execute": "qmp_capabilities"})
        if "error" in capabilities:
            raise RuntimeError(capabilities)
        result = request(stream, json.loads(args.command))
        print(json.dumps(result, indent=2))
        return int("error" in result)


if __name__ == "__main__":
    raise SystemExit(main())
