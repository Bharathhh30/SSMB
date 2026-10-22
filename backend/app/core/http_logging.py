import json
import logging
from time import perf_counter
from uuid import uuid4

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("app.http")


class RequestLoggingMiddleware:
    """Attach a server-generated request ID and emit privacy-safe JSON access logs."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid4().hex
        started_at = perf_counter()
        status_code = 500
        response_started = False
        error_type: str | None = None

        async def send_with_request_id(message: Message) -> None:
            nonlocal response_started, status_code
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != b"x-request-id"
                ]
                headers.append((b"x-request-id", request_id.encode("ascii")))
                message = {**message, "headers": headers}
            await send(message)

        completed = False
        failed = False
        try:
            await self.app(scope, receive, send_with_request_id)
            completed = True
        except Exception as error:
            failed = True
            error_type = type(error).__name__
            if response_started:
                raise
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
            await response(scope, receive, send_with_request_id)
        finally:
            if completed or failed:
                route = getattr(scope.get("route"), "path", "unmatched")
                record = {
                    "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                    "event": "http.request",
                    "failed": failed,
                    "method": scope.get("method", "UNKNOWN"),
                    "request_id": request_id,
                    "route": route,
                    "status_code": status_code,
                }
                if error_type is not None:
                    record["error_type"] = error_type
                level = logging.ERROR if status_code >= 500 else logging.INFO
                logger.log(level, json.dumps(record, separators=(",", ":"), sort_keys=True))
