#!/usr/bin/env python3
"""Loopback HTTP server for chords-agent (GET /progressions, /song, /health)."""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.error import URLError
from urllib.request import Request, urlopen


DEFAULT_PORT = 17891
APP_NAME = "songwriter"


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
        if path.is_file():
            return path.read_text()
    return None


def write_snapshot(file_name: str, contents: str) -> bool:
    directory = home_dir()
    try:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / file_name).write_text(contents)
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
    return text


class AgentHandler(BaseHTTPRequestHandler):
    server_version = "chords-agent/1"

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def _json(self, status: int, body: str, head_only: bool = False) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        if not head_only:
            self.wfile.write(payload)

    def _document(self, path: str) -> Optional[str]:
        port = int(self.server.server_address[1])
        if path in ("/", "/index.json"):
            return (
                '{"app":"%s","port":%d,"endpoints":{'
                '"/health":"liveness",'
                '"/song":"full song including empty slots",'
                '"/progressions":"chords that have been added, by section"}}'
                % (APP_NAME, port)
            )
        if path == "/health":
            return '{"ok":true,"app":"%s","port":%d}' % (APP_NAME, port)
        if path == "/song":
            return snapshot_body("song.json")
        if path == "/progressions":
            return snapshot_body("progressions.json")
        return None

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        body = self._document(path)
        if body is None:
            self._json(404, '{"error":"not found"}')
            return
        self._json(200, body)

    def do_HEAD(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        body = self._document(path)
        if body is None:
            self._json(404, '{"error":"not found"}', head_only=True)
            return
        self._json(200, body, head_only=True)

    def do_POST(self) -> None:  # noqa: N802
        self._json(405, '{"error":"only GET is supported"}')


def serve(port: int, home: Optional[Path] = None) -> int:
    if home is not None:
        os.environ["CHORDS_AGENT_HOME"] = str(home)
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", port), AgentHandler)
    except OSError as exc:
        sys.stderr.write(f"agent-server: bind 127.0.0.1:{port} failed: {exc}\n")
        return 2
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
