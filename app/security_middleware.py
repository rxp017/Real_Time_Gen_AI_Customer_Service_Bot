"""Clock-driven bounded request budgets, origin checks and browser response headers."""

import hashlib
import os
from collections import deque
from threading import RLock

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from core.clock import get_clock
from core.config import get_config

CSP = "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"


class CustomerBoundary:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.clock = None
        self.lock = RLock()
        self.buckets: dict[str, deque[float]] = {}

    def _admit(self, scope: Scope, headers: dict[bytes, bytes]) -> bool:
        cfg, clock = get_config(), get_clock()
        now = clock.monotonic()
        window = float(cfg.get("web.rate_window_seconds"))
        limit = int(cfg.get("web.requests_per_window"))
        ip = str((scope.get("client") or ("unknown",))[0])
        key = hashlib.sha256(headers.get(b"x-api-key", b"anonymous")).hexdigest()
        keys = [("ip:" + ip, limit), ("key:" + key, limit)]
        if scope["path"] == "/uploads" and scope["method"] == "POST":
            keys.append(("upload:" + ip, int(cfg.get("web.uploads_per_window"))))
        with self.lock:
            if self.clock is not clock:
                self.buckets.clear()
                self.clock = clock
            for bucket_key in list(self.buckets):
                bucket = self.buckets[bucket_key]
                while bucket and bucket[0] <= now - window:
                    bucket.popleft()
                if not bucket:
                    del self.buckets[bucket_key]
            if len(self.buckets) + len(keys) > int(cfg.get("web.max_rate_buckets")):
                return False
            if any(len(self.buckets.get(k, ())) >= cap for k, cap in keys):
                return False
            for bucket_key, _ in keys:
                self.buckets.setdefault(bucket_key, deque()).append(now)
        return True

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        cfg, headers = get_config(), dict(scope["headers"])
        origin = headers.get(b"origin", b"").decode("latin1")
        same_origin = scope.get("scheme", "http") + "://" + headers.get(b"host", b"").decode("latin1")
        allowed = set(cfg.get("web.allowed_origins")) | {same_origin}
        external = os.getenv("RENDER_EXTERNAL_URL", "")
        if external:
            allowed.add(external.rstrip("/"))
        accepted_origin = bool(origin and origin in allowed)
        async def secure_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                extra = [(b"content-security-policy", CSP.encode()), (b"x-content-type-options", b"nosniff"),
                         (b"referrer-policy", b"no-referrer"), (b"cache-control", b"no-store")]
                if accepted_origin:
                    extra.extend([(b"access-control-allow-origin", origin.encode("latin1")), (b"vary", b"Origin")])
                message = {**message, "headers": list(message.get("headers", [])) + extra}
            await send(message)
        if origin and not accepted_origin:
            await JSONResponse({"detail": "Origin is not allowed"}, status_code=403)(scope, receive, secure_send)
            return
        if scope["method"] == "OPTIONS":
            await JSONResponse({}, headers={"Access-Control-Allow-Methods": "GET, POST", "Access-Control-Allow-Headers": "content-type, x-api-key"})(scope, receive, secure_send)
            return
        if scope["path"].startswith(("/query", "/uploads", "/tickets")) and not self._admit(scope, headers):
            await JSONResponse({"detail": "Request rate limit reached; retry later"}, status_code=429,
                               headers={"Retry-After": str(int(cfg.get("web.rate_window_seconds")))})(scope, receive, secure_send)
            return
        if scope["method"] == "POST" and scope["path"] != "/uploads":
            data = bytearray()
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                data.extend(message.get("body", b""))
                if len(data) > int(cfg.get("web.max_json_bytes")):
                    await JSONResponse({"detail": "Request body too large"}, status_code=413)(scope, receive, secure_send)
                    return
                if not message.get("more_body", False):
                    break
            delivered = False
            async def replay() -> Message:
                nonlocal delivered
                if delivered:
                    return await receive()
                delivered = True
                return {"type": "http.request", "body": bytes(data), "more_body": False}
            await self.app(scope, replay, secure_send)
        else:
            await self.app(scope, receive, secure_send)
