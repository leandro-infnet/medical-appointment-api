"""CORS, headers e limite local de requisições, com estado por execução."""
from collections import deque
from math import ceil
from threading import Lock
from time import monotonic
from typing import Callable

from fastapi import Request
from starlette.datastructures import MutableHeaders
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

AUTH_PATHS = {"/auth/token", "/auth/m2m/token", "/auth/mfa"}
WINDOW_SECONDS = 60


class RateLimiter:
    def __init__(self, login_limit: int, general_limit: int, clock: Callable[[], float] = monotonic):
        self.limits = {"credenciais": login_limit, "geral": general_limit}
        self.clock = clock
        self.requests: dict[tuple[str, str], deque[float]] = {}
        self.lock = Lock()

    def retry_after(self, peer: str, bucket: str) -> int:
        now = self.clock()
        with self.lock:
            # Remove clientes inativos para não acumular uma entrada por IP para sempre.
            expired = [key for key, times in self.requests.items() if times[-1] <= now - WINDOW_SECONDS]
            for key in expired:
                del self.requests[key]
            times = self.requests.setdefault((peer, bucket), deque())
            while times and times[0] <= now - WINDOW_SECONDS:
                times.popleft()
            if len(times) >= self.limits[bucket]:
                return max(1, ceil(WINDOW_SECONDS - (now - times[0])))
            times.append(now)
            return 0


class NetworkMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def limited_app(self, scope: Scope, receive: Receive, send: Send):
        request = Request(scope)
        peer = request.client.host if request.client else "sem-endereco"
        bucket = "credenciais" if request.url.path.rstrip("/") in AUTH_PATHS else "geral"
        retry = request.app.state.rate_limiter.retry_after(peer, bucket)
        if retry:
            response = JSONResponse({"detail": "Limite de requisições excedido."}, status_code=429,
                headers={"Retry-After": str(retry), "Cache-Control": "no-store"})
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_headers(message: Message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Frame-Options"] = "DENY"
                headers["X-Content-Type-Options"] = "nosniff"
                if scope["scheme"] == "https":
                    headers["Strict-Transport-Security"] = "max-age=31536000"
            await send(message)

        # A configuração vem do lifespan; não exige segredos ao importar app.main.
        # CORSMiddleware é stateless; usar o estado do arranque também isola os testes.
        settings = Request(scope).app.state.settings
        cors = CORSMiddleware(self.limited_app, allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type"], expose_headers=["Retry-After"],
            allow_credentials=False)
        await cors(scope, receive, send_headers)
