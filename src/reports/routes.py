from src.core.asgi import APIArchitecture, RouterExtended


def get_reports_router() -> RouterExtended:
    return RouterExtended(
        prefix=f"/{APIArchitecture.REST}/{{version}}/reports",
        tags=["Companies"],
    )
