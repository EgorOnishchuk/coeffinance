from src.core.asgi import Architecture, ExtendedRouter


def get_analytics_router() -> ExtendedRouter:
    return ExtendedRouter(
        prefix=f"/{Architecture.JSON_API}/{{version}}/analytics",
        tags=["Companies"],
    )
