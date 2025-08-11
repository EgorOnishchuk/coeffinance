from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dishka import AsyncContainer
from fastapi import APIRouter
from fastapi_users import FastAPIUsers
from starlette.routing import BaseRoute

from src.core.routers import DishkaRouter, OpenAPIEditor, RouterManager
from src.core.schemas import Error, JSONDict
from src.users.deps import MultiFrontend
from src.users.schemas import UserCreate, UserRead, UserUpdate


class UserRouterManager(RouterManager):
    me_routes: int = 2

    async def attach(self) -> None:
        router = DishkaRouter(prefix="/users", tags=["users"])
        container: AsyncContainer = self.app.state.dishka_container
        fastapi_users = await container.get(FastAPIUsers)

        for sub_router in (
            fastapi_users.get_register_router(UserRead, UserCreate),
            fastapi_users.get_auth_router(await container.get(MultiFrontend), requires_verification=True),
            fastapi_users.get_verify_router(UserRead),
            fastapi_users.get_reset_password_router(),
        ):
            router.include_router(sub_router, prefix="/auth", tags=["auth"])
        router.include_router(APIRouter(routes=self._get_me_routes(fastapi_users=fastapi_users)))

        self.app.include_router(router)
        self.app.openapi_schema = self._get_updated_openapi()

    def _get_me_routes(self, fastapi_users: FastAPIUsers) -> list[BaseRoute]:
        return fastapi_users.get_users_router(UserRead, UserUpdate, requires_verification=True).routes[: self.me_routes]

    def _get_updated_openapi(self) -> JSONDict:
        """
        Overrides the error format that fastapi-users hardcodes when it generates routes programmatically.
        """
        editor = OpenAPIEditor(openapi=self.app.openapi())

        editor.override_schemas(models=("ErrorModel", "HTTPValidationError"), source=Error.model_json_schema())
        editor.remove_elements(target="examples")

        return editor.openapi
