# pyright: reportUnusedFunction=false

from typing import Annotated

from dishka import FromDishka
from fastapi import Depends, Query

from src.companies.schemas import (
    AllCompaniesSearch,
    CompanyRead,
    UserCompaniesSearch,
)
from src.companies.service import CompanyService
from src.core.asgi import Architecture, ExtendedRouter
from src.core.schemas import (
    BaseCursorPage,
    BaseOffsetPage,
    CursorSortingSearch,
    OffsetSortingSearch,
)
from src.users.db.models import DBUserProtocol
from src.users.deps import get_authenticated


def get_company_router() -> ExtendedRouter:
    router = ExtendedRouter(
        prefix=f"/{Architecture.JSON_API}/{{version}}/companies",
        tags=[
            "companies",
        ],
    )

    @router.get("/my")
    async def get_my_companies(
        user: Annotated[
            DBUserProtocol,
            Depends(get_authenticated),
        ],
        service: FromDishka[CompanyService],
        conditions: Annotated[OffsetSortingSearch, Query()],
    ) -> BaseOffsetPage[CompanyRead]:
        return await service.get_by_user(
            clauses=UserCompaniesSearch(
                user_nickname=user.nickname,
                **conditions.model_dump(),
            )
        )

    @router.get(
        "/all",
        dependencies=(Depends(get_authenticated),),
    )
    async def get_all_companies(
        service: FromDishka[CompanyService],
        conditions: Annotated[AllCompaniesSearch, Query()],
    ) -> BaseCursorPage[CompanyRead]:
        return await service.get_all(
            clauses=CursorSortingSearch(**conditions.model_dump())
        )

    return router
