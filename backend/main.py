from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

from backend.api.chatbot import ask_assistant
from backend.api.eligibility import check_eligibility
from backend.api.farmer import validate_profile
from backend.api.schemes import list_schemes
from backend.models.farmer import ProfileError
from backend.services.recommendation import CropDataError, recommend_crop


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
MAX_BODY_BYTES = 64 * 1024
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
LOGGER = logging.getLogger("agrisahay")


class AgriSahayHandler(BaseHTTPRequestHandler):
    server_version = "AgriSahay/1.0"

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/schemes":
            self._json_response(200, {"schemes": list_schemes()})
            return
        if path == "/health":
            self._json_response(200, {"status": "ok"})
            return
        asset = "index.html" if path in ("/", "/index.html") else path.lstrip("/")
        if asset in {"index.html", "app.css", "app.js"}:
            self._file_response(FRONTEND_ROOT / asset)
            return
        self._json_response(404, {"error": "Not found."})

    def do_POST(self) -> None:
        routes = {
            "/api/match": self._match,
            "/api/eligibility": self._match,
            "/api/assistant": self._assistant,
            "/api/crop-recommendation": self._crop_recommendation,
        }
        handler = routes.get(urlparse(self.path).path)
        if handler is None:
            self._json_response(404, {"error": "Not found."})
            return
        try:
            handler(self._read_json())
        except (ProfileError, ValueError) as error:
            self._json_response(400, {"error": str(error)})
        except CropDataError as error:
            LOGGER.exception("Crop recommendation data error")
            self._json_response(503, {"error": str(error)})
        except Exception:
            LOGGER.exception("Unhandled request failure for %s", self.path)
            self._json_response(500, {"error": "The request could not be completed. Check the server log."})

    def _match(self, payload: object) -> None:
        self._json_response(200, check_eligibility(payload))

    def _assistant(self, payload: object) -> None:
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        self._json_response(
            200,
            ask_assistant(payload.get("message"), payload.get("profile"), payload.get("language", "en")),
        )

    def _crop_recommendation(self, payload: object) -> None:
        self._json_response(200, recommend_crop(payload))

    def _read_json(self) -> object:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Content-Length must be a valid integer.") from error
        if length <= 0 or length > MAX_BODY_BYTES:
            raise ValueError(f"Request body must be between 1 and {MAX_BODY_BYTES} bytes.")
        try:
            return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError("Request body must contain valid UTF-8 JSON.") from error

    def _file_response(self, path: Path) -> None:
        try:
            body = path.read_bytes()
        except OSError:
            self._json_response(404, {"error": "Frontend asset not found."})
            return
        content_type = "text/html; charset=utf-8" if path.suffix == ".html" else (
            "text/css; charset=utf-8" if path.suffix == ".css" else "text/javascript; charset=utf-8"
        )
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json_response(self, status: int, value: object) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        LOGGER.info("%s - %s", self.address_string(), format % args)


def main() -> None:
    host = os.environ.get("AGRISAHAY_HOST", "127.0.0.1")
    port = int(os.environ.get("AGRISAHAY_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), AgriSahayHandler)
    LOGGER.info("AgriSahay listening at http://%s:%d", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("Shutting down")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()