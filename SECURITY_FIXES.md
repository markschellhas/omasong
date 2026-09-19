# Rate limiter fixes for `agent-server.py`

Two low-severity fixes identified in a security review of the local loopback HTTP API server. Both are scoped to avoid any noticeable change to normal/legitimate usage (this server has no real load in practice — the QML plugin doesn't even call it over HTTP; only the `chords-agent` CLI does, one request at a time).

## Fix 1 — exempt `/health` from the rate limiter

**Problem:** `do_GET` and `do_HEAD` both call `self._rate_limited()` unconditionally before dispatching, so health checks consume tokens from the same 60-token/30-per-sec bucket as real data requests (`/song`, `/progressions`, `/`, `/index.json`). A tight health-check loop (e.g. `watch` or a monitoring script) could crowd out legitimate data requests with spurious 429s.

**Fix:** compute the path first and skip the rate-limit check specifically for `/health`, leaving every other path rate-limited exactly as before.

```python
def do_GET(self) -> None:  # noqa: N802
    path = self.path.split("?", 1)[0]
    if path != "/health" and self._rate_limited():
        self._json(429, '{"error":"rate limit exceeded"}')
        return
    body, err = self._document(path)
    # ...unchanged from here...

def do_HEAD(self) -> None:  # noqa: N802
    path = self.path.split("?", 1)[0]
    if path != "/health" and self._rate_limited():
        self._json(429, '{"error":"rate limit exceeded"}', head_only=True)
        return
    body, err = self._document(path)
    # ...unchanged from here...
```

(Was: unconditional `if self._rate_limited(): ...` before `path` was even computed. Match whatever the current variable name/order is in `_document()`'s existing path normalization — reuse the same `self.path.split("?", 1)[0]` pattern already used elsewhere in the file rather than introducing a new one.)

## Fix 2 — bound concurrent connections + idle-connection timeout

**Problem:** the server uses a plain `http.server.ThreadingHTTPServer`, which spawns one unbounded OS thread per accepted TCP connection with no cap and no read timeout. A burst of many connections — even idle/slow ones that never send a full request — can exhaust threads/file descriptors *before* the rate limiter (which only runs inside request handling, after a thread is already spawned) ever gets a chance to reject anything.

**Fix:**

1. Add a socket-level read timeout on the request handler class:

```python
class AgentHandler(BaseHTTPRequestHandler):
    timeout = 5  # seconds; StreamRequestHandler.setup() calls connection.settimeout(self.timeout)
    ...
```

2. Add a bounded-concurrency wrapper around `ThreadingHTTPServer` and use it in `serve()`:

```python
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
```

Then in `serve()`, replace:

```python
server = ThreadingHTTPServer(("127.0.0.1", port), AgentHandler)
```

with:

```python
server = BoundedThreadingHTTPServer(("127.0.0.1", port), AgentHandler)
```

Notes:
- The semaphore is released in `process_request_thread` (which runs *inside* the spawned thread, when the request is actually finished), not in `process_request` (which returns immediately after spawning the thread) — releasing in the wrong place would make the cap meaningless.
- `blocking=False` + immediate `shutdown_request` means a connection over the cap is dropped instantly rather than queued, so there's no added latency for the normal case of a handful of local callers.
- 32 concurrent connections is far above anything realistic local usage would ever hit — this is purely a ceiling against runaway floods.
- `import threading` needs to be added if not already imported.

## Known test conflict — needs a matching fix

`tests/agent_tests.py::test_rate_limit_returns_429` (around line 406) currently bursts requests against `/health` specifically, expecting a 429 to eventually appear. Once `/health` is exempted (Fix 1), that test can never pass as written — the loop will exhaust and raise `SystemExit("expected rate limit 429 after burst")`.

**Recommended fix:** retarget that test at `/song` (or `/progressions`) instead of `/health`, so it still verifies the limiter works on real data endpoints. Optionally add a small additional assertion that repeated `/health` requests never return 429, to lock in the exemption behavior.

## Validation already done (in an isolated scratchpad copy, not the real repo)

- `python3 -c "import ast; ast.parse(open('agent-server.py').read())"` — syntax OK.
- Ran the real suite (`python3 tests/agent_tests.py`) against the patched copy: 8/9 passed (song snapshot, progressions snapshot, health-down, --live-down, missing-snapshot, live, health-after-stop, invalid-snapshot-503); only `test_rate_limit_returns_429` failed, for the expected reason described above.

The fully patched file (before the test fix) is available at:
`/tmp/claude-1000/-home-umain--config-omarchy-plugins-songwriter/14217e1a-e127-4bef-bd9e-fd7c3ed1d858/scratchpad/repo-copy/agent-server.py`
for reference/diffing if useful.
