"""Chrome native messaging: every message is a 4-byte native-endian length + UTF-8 JSON,
on stdin (requests) and stdout (replies). stdout must carry nothing else.
"""
import json, struct, sys, traceback


def read_message():
    header = sys.stdin.buffer.read(4)
    if len(header) < 4:
        return None   # Chrome closed the pipe
    (length,) = struct.unpack("=I", header)
    return json.loads(sys.stdin.buffer.read(length))

def send_message(msg):
    body = json.dumps(msg).encode()
    sys.stdout.buffer.write(struct.pack("=I", len(body)) + body)
    sys.stdout.buffer.flush()

def serve(handle):
    """Answer each request with handle(msg); errors go back as {"error": ...} and to stderr."""
    while (msg := read_message()) is not None:
        try:
            send_message(handle(msg))
        except Exception as e:
            traceback.print_exc(file=sys.stderr)   # launcher sends stderr to ~/Library/Logs/captcha-paster-host.log
            send_message({"error": f"{type(e).__name__}: {e}"})
