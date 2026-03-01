import json
import os
import threading
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
EVENT_LOG_FILE = BASE_DIR / "data" / "events.jsonl"
MAX_EVENTS = 200

events = []
events_lock = threading.Lock()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_data_dir() -> None:
    EVENT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_events() -> None:
    ensure_data_dir()
    if not EVENT_LOG_FILE.exists():
        return

    loaded = []
    with EVENT_LOG_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                loaded.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    with events_lock:
        events.clear()
        events.extend(reversed(loaded[-MAX_EVENTS:]))


def append_event(event: dict) -> None:
    ensure_data_dir()
    with EVENT_LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")


def record_event(body: str, headers: dict, path: str) -> dict:
    try:
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError:
        payload = {"raw_body": body}

    event = {
        "id": str(uuid.uuid4()),
        "received_at": utc_now_iso(),
        "path": path,
        "method": "POST",
        "content_type": headers.get("Content-Type", ""),
        "user_agent": headers.get("User-Agent", ""),
        "payload": payload,
    }

    with events_lock:
        events.insert(0, event)
        del events[MAX_EVENTS:]

    append_event(event)
    return event


def clear_events() -> None:
    with events_lock:
        events.clear()
    ensure_data_dir()
    EVENT_LOG_FILE.write_text("", encoding="utf-8")


def read_static_file(filename: str, content_type: str) -> tuple[bytes, str]:
    path = STATIC_DIR / filename
    return path.read_bytes(), content_type


class DemoHandler(BaseHTTPRequestHandler):
    server_version = "WebhookReceiverDemo/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path

        if route == "/":
            body, content_type = read_static_file("index.html", "text/html; charset=utf-8")
            self.respond_bytes(HTTPStatus.OK, body, content_type)
            return

        if route == "/static/app.js":
            body, content_type = read_static_file("app.js", "application/javascript; charset=utf-8")
            self.respond_bytes(HTTPStatus.OK, body, content_type)
            return

        if route == "/static/styles.css":
            body, content_type = read_static_file("styles.css", "text/css; charset=utf-8")
            self.respond_bytes(HTTPStatus.OK, body, content_type)
            return

        if route == "/api/events":
            with events_lock:
                payload = {"events": events}
            self.respond_json(HTTPStatus.OK, payload)
            return

        if route == "/api/health":
            self.respond_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "events": len(events),
                    "timestamp": utc_now_iso(),
                },
            )
            return

        self.respond_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path

        if route == "/webhook":
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8") if length else ""
            event = record_event(body, dict(self.headers.items()), route)
            self.respond_json(
                HTTPStatus.CREATED,
                {
                    "message": "Webhook received",
                    "event_id": event["id"],
                    "received_at": event["received_at"],
                },
            )
            return

        if route == "/api/events/clear":
            clear_events()
            self.respond_json(HTTPStatus.OK, {"message": "Event log cleared"})
            return

        self.respond_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def log_message(self, format: str, *args) -> None:
        return

    def respond_json(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.respond_bytes(status, body, "application/json; charset=utf-8")

    def respond_bytes(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    load_events()
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), DemoHandler)
    print(f"Webhook Receiver demo running at http://127.0.0.1:{port}")
    print(f"POST webhook payloads to http://127.0.0.1:{port}/webhook")
    server.serve_forever()


if __name__ == "__main__":
    main()
