from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp


class VersionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, version: str) -> None:
        super().__init__(app)
        self.version = version

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Version"] = self.version

        return response
