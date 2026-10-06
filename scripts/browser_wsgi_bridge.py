"""Local screenshot fallback when OS sandboxing forbids loopback browser sockets.

Requests from Playwright are dispatched to the real Flask WSGI app over stdin/stdout.
Cookies stay in the browser, CSRF stays enabled, and the normal local database is used.
This is a verification utility, not an alternative production server.
"""

import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402


def main():
    app = create_app()
    client = app.test_client(use_cookies=False)
    print(json.dumps({"ready": True}), flush=True)
    for line in sys.stdin:
        payload = json.loads(line)
        response = client.open(path=payload["path"], method=payload["method"],
                               headers=payload["headers"],
                               data=base64.b64decode(payload["body"]),
                               base_url="http://127.0.0.1:5000", follow_redirects=False)
        headers = {}
        for name in response.headers.keys():
            headers[name.lower()] = "\n".join(response.headers.getlist(name))
        print(json.dumps({"id": payload["id"], "status": response.status_code,
                          "headers": headers,
                          "body": base64.b64encode(response.data).decode("ascii")}), flush=True)


if __name__ == "__main__":
    main()
