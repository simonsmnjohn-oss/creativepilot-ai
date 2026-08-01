from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .outreach import build_outreach_drafts, parse_outreach_request, serialize_draft, summarize_pipeline


class OutreachHandler(BaseHTTPRequestHandler):
    """Small stdlib HTTP API for creating manual-review outreach drafts."""

    def do_GET(self) -> None:  # noqa: N802 - stdlib method name
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - stdlib method name
        if self.path != "/outreach/drafts":
            self._send_json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            request = parse_outreach_request(payload)
            drafts = build_outreach_drafts(request)
            self._send_json(
                200,
                {
                    "summary": summarize_pipeline(drafts),
                    "drafts": [serialize_draft(draft) for draft in drafts],
                },
            )
        except (json.JSONDecodeError, ValueError) as exc:
            self._send_json(400, {"error": str(exc)})

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), OutreachHandler)


def main() -> None:
    server = create_server()
    print("CreativePilot AI listening on http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
