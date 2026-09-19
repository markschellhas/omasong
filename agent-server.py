#!/usr/bin/env python3
"""Loopback HTTP server for chords-agent (GET /progressions, /song, /health)."""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.error import URLError
from urllib.request import Request, urlopen


DEFAULT_PORT = 17891
APP_NAME = "songwriter"
MAX_SNAPSHOT_BYTES = 1_500_000
# Token bucket: refill_rate tokens/sec, burst capacity.
RATE_REFILL_PER_SEC = 30.0
RATE_BURST = 60.0


def home_dir() -> Path:
    override = os.environ.get("CHORDS_AGENT_HOME")
    if override:
        return Path(override)
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / APP_NAME
    home = os.environ.get("HOME")
    if home:
        return Path(home) / ".config" / APP_NAME
    return Path(APP_NAME)


def search_dirs() -> list[Path]:
    return [home_dir()]


def read_snapshot(file_name: str) -> Optional[str]:
    for directory in search_dirs():
        path = directory / file_name
        if not path.is_file():
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > MAX_SNAPSHOT_BYTES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if len(text.encode("utf-8")) > MAX_SNAPSHOT_BYTES:
            continue
        return text
    return None


def write_snapshot(file_name: str, contents: str) -> bool:
    directory = home_dir()
    try:
        encoded = contents.encode("utf-8")
        if len(encoded) > MAX_SNAPSHOT_BYTES:
            return False
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / file_name
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{file_name}.",
            suffix=".tmp",
            dir=str(directory),
        )
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
        return True
    except OSError:
        return False


def parse_port_json(text: str) -> int:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return -1
    port = data.get("port") if isinstance(data, dict) else None
    try:
        parsed = int(port)
    except (TypeError, ValueError):
        return -1
    if parsed < 1 or parsed > 65535:
        return -1
    return parsed


def env_port() -> Optional[int]:
    raw = os.environ.get("CHORDS_AGENT_PORT")
    if raw is None or raw == "":
        return None
    try:
        parsed = int(raw)
    except ValueError:
        return None
    if parsed < 0 or parsed > 65535:
        return None
    return parsed


def discover_agent_port() -> int:
    env = env_port()
    if env is not None:
        return env
    meta = read_snapshot("agent-api.json")
    if meta is not None:
        recorded = parse_port_json(meta)
        if recorded > 0:
            return recorded
    return DEFAULT_PORT


def bind_port() -> int:
    env = env_port()
    if env is not None:
        return env
    return DEFAULT_PORT


def http_get_local(port: int, path: str, timeout: float = 0.35) -> tuple[int, str]:
    if port <= 0:
        return 0, ""
    url = f"http://127.0.0.1:{port}{path}"
    req = Request(url, method="GET")
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return int(resp.status), body
    except (URLError, TimeoutError, OSError, ValueError):
        return 0, ""


def agent_is_live() -> bool:
    status, body = http_get_local(discover_agent_port(), "/health")
    return status == 200 and '"ok":true' in body


def read_agent_document(route: str, snapshot_name: str) -> Optional[str]:
    status, body = http_get_local(discover_agent_port(), route)
    if status == 200 and body:
        return body
    snap = read_snapshot(snapshot_name)
    if snap is not None and snap != "":
        return snap
    return None


def snapshot_body(name: str) -> Optional[str]:
    text = read_snapshot(name)
    if text is None or text == "":
        return None
    try:
        json.loads(text)
    except json.JSONDecodeError:
        return None
    return text


class RateLimiter:
    """Process-wide token bucket for loopback GET flood protection."""

    def __init__(self, refill_per_sec: float, burst: float) -> None:
        self.refill_per_sec = refill_per_sec
        self.burst = burst
        self.tokens = burst
        self.updated = time.monotonic()
        self.lock = threading.Lock()

    def allow(self) -> bool:
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.updated
            self.updated = now
            self.tokens = min(self.burst, self.tokens + elapsed * self.refill_per_sec)
            if self.tokens < 1.0:
                return False
            self.tokens -= 1.0
            return True


class AgentHandler(BaseHTTPRequestHandler):
    server_version = "chords-agent/1"
    timeout = 5  # seconds; StreamRequestHandler.setup() calls connection.settimeout(self.timeout)

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def _json(self, status: int, body: str, head_only: bool = False) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.send_header("Cache-Control", "no-store")
        if status == 429:
            self.send_header("Retry-After", "1")
        self.end_headers()
        if not head_only:
            self.wfile.write(payload)

    def _rate_limited(self) -> bool:
        limiter = getattr(self.server, "rate_limiter", None)
        if limiter is None:
            return False
        return not limiter.allow()

    def _document(self, path: str) -> tuple[Optional[str], Optional[int]]:
        """Return (body, error_status). error_status is set when body is None and not 404."""
        port = int(self.server.server_address[1])
        if path in ("/", "/index.json"):
            return (
                '{"app":"%s","port":%d,"endpoints":{'
                '"/health":"liveness",'
                '"/song":"full song including empty slots",'
                '"/progressions":"chords that have been added, by section"}}'
                % (APP_NAME, port),
                None,
            )
        if path == "/health":
            return '{"ok":true,"app":"%s","port":%d}' % (APP_NAME, port), None
        if path == "/song":
            body = snapshot_body("song.json")
            if body is None:
                # Distinguish missing vs torn/invalid for clients that care.
                raw = read_snapshot("song.json")
                if raw is not None and raw != "":
                    return None, 503
                return None, 404
            return body, None
        if path == "/progressions":
            body = snapshot_body("progressions.json")
            if body is None:
                raw = read_snapshot("progressions.json")
                if raw is not None and raw != "":
                    return None, 503
                return None, 404
            return body, None
        return None, 404

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path != "/health" and self._rate_limited():
            self._json(429, '{"error":"rate limit exceeded"}')
            return
        body, err = self._document(path)
        if body is None:
            if err == 503:
                self._json(503, '{"error":"snapshot unavailable"}')
            else:
                self._json(404, '{"error":"not found"}')
            return
        self._json(200, body)

    def do_HEAD(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path != "/health" and self._rate_limited():
            self._json(429, '{"error":"rate limit exceeded"}', head_only=True)
            return
        body, err = self._document(path)
        if body is None:
            if err == 503:
                self._json(503, '{"error":"snapshot unavailable"}', head_only=True)
            else:
                self._json(404, '{"error":"not found"}', head_only=True)
            return
        self._json(200, body, head_only=True)

    def do_POST(self) -> None:  # noqa: N802
        self._json(405, '{"error":"only GET is supported"}')


MAX_CONCURRENT_CONNECTIONS = 32


class BoundedThreadingHTTPServer(ThreadingHTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._semaphore = threading.BoundedSemaphore(MAX_CONCURRENT_CONNECTIONS)

    def process_request(self, request, client_address):
        if not self._semaphore.acquire(blocking=False):
            # Already at the cap — drop the connection immediately, don't queue.
            self.shutdown_request(request)
            return
        super().process_request(request, client_address)

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._semaphore.release()


def serve(port: int, home: Optional[Path] = None) -> int:
    if home is not None:
        os.environ["CHORDS_AGENT_HOME"] = str(home)
    try:
        httpd = BoundedThreadingHTTPServer(("127.0.0.1", port), AgentHandler)
    except OSError as exc:
        sys.stderr.write(f"agent-server: bind 127.0.0.1:{port} failed: {exc}\n")
        return 2
    httpd.rate_limiter = RateLimiter(RATE_REFILL_PER_SEC, RATE_BURST)  # type: ignore[attr-defined]
    bound = int(httpd.server_address[1])
    write_snapshot("agent-api.json", json.dumps({"port": bound}))

    def stop(_signum=None, _frame=None) -> None:
        threading.Thread(target=httpd.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Loopback chords-agent HTTP server")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--home", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.home is not None:
        os.environ["CHORDS_AGENT_HOME"] = str(args.home)
    port = args.port if args.port is not None else bind_port()
    return serve(port, args.home)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
