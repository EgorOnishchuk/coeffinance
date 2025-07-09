from fastapi import Request, Response
from pydantic_extra_types.semantic_version import SemanticVersion
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp


class VersionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, version: SemanticVersion) -> None:
        super().__init__(app)
        self.version: SemanticVersion = version

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Version"] = str(self.version)

        return response
