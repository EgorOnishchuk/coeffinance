from http import HTTPStatus

from fastapi import APIRouter

from src.core.asgi import Architecture, ExtendedRouter
from src.core.schemas import PublicError
from src.core.utils.openapi import ResponseEditor
from src.users.deps import get_fastapi_users
from src.users.schemas import UserCreate, UserRead, UserUpdate


def get_user_router() -> ExtendedRouter:
    router = ExtendedRouter(
        prefix=f"/{Architecture.JSON_API}/{{version}}/users",
        tags=["users"],
    )

    fastapi_users = get_fastapi_users()

    for sub_router in (
        fastapi_users.get_register_router(UserRead, UserCreate),  # type: ignore[type-var] # pyright: ignore[reportArgumentType]
        fastapi_users.get_verify_router(UserRead),  # type: ignore[type-var] # pyright: ignore[reportArgumentType]
        fastapi_users.get_reset_password_router(),
    ):
        router.include_router(sub_router, prefix="/auth", tags=["auth"])

    for backend in fastapi_users.authenticator.backends:
        auth_router = fastapi_users.get_auth_router(
            backend,
            requires_verification=True,
        )

        router.include_router(
            auth_router,
            prefix=f"/auth/{backend.name}",
            tags=["auth"],
        )

    profile_routes = 2
    router.include_router(
        APIRouter(
            routes=fastapi_users.get_users_router(
                UserRead,  # type: ignore[type-var] # pyright: ignore[reportArgumentType]
                UserUpdate,
                requires_verification=True,
            ).routes[:profile_routes]
        )
    )

    editor = ResponseEditor(
        _responses=tuple(route.responses for route in router.routes)  # type: ignore[attr-defined] # pyright: ignore[reportAttributeAccessIssue] # Undocumented attr.
    )
    editor.override_error(error=PublicError, code=HTTPStatus.BAD_REQUEST)
    editor.remove_examples()

    return router
