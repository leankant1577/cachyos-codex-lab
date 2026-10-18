"""Type a synthetic password only into the task's private QEMU test console."""
import json
import socket
import time

from vm_qmp import request


def main():
    with socket.create_connection(("127.0.0.1", 55332), timeout=10) as connection:
        stream = connection.makefile("rwb")
        json.loads(stream.readline())
        assert "return" in request(stream, {"execute": "qmp_capabilities"})
        blocks = request(stream, {"execute": "query-block"})["return"]
        names = [str(block.get("inserted", {}).get("file", "")) for block in blocks]
        assert any("install-smoke.qcow2" in name for name in names)
        assert any("cachyos-codex-260809" in name and name.endswith(".iso") for name in names)
        for _ in range(2):
            for character in "codextest12345678" + "\n":
                key = "ret" if character == "\n" else character
                events = [{"type": "key", "data": {"down": down,
                           "key": {"type": "qcode", "data": key}}} for down in (True, False)]
                result = request(stream, {"execute": "input-send-event", "arguments": {"events": events}})
                assert "return" in result, result
                time.sleep(0.08)
            time.sleep(1)
    print("Synthetic password sent to private VM only; verify guest receipt and delete it.")


if __name__ == "__main__":
    main()
