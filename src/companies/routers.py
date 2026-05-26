# pyright: reportUnusedFunction=false

from typing import Annotated

from dishka import FromDishka
from fastapi import Depends, Query

from src.companies.infrastructure.api_clients import (
    CompanyAPIClient,
    RussianCompanyLegalsAPIFetcher,
)
from src.companies.schemas import (
    AllCompaniesPagination,
    Company,
    CompanyIdentity,
    Country,
    CompanyIdentity,
    RussianCompanyIdentity,
    UserCompaniesPagination,
)
from src.companies.services import (
    CompanyService,
)
from src.core.asgi import APIArchitecture, RouterExtended, HTTPStatus
from src.core.validators import (
    CursorPage,
    CursorSortedPagination,
    OffsetPage,
    OffsetSortedPagination,
)
from src.users.deps import get_authenticated
from src.users.infrastructure.db_models import DBUserProtocol


def company_router() -> RouterExtended:
    router = RouterExtended(
        prefix=f"/{APIArchitecture.REST}/{{version}}/companies",
        tags=[
            "companies",
        ],
    )

    @router.get(
        "/search",
        dependencies=(Depends(get_authenticated),),
    )
    async def get_one(
        service: FromDishka[CompanyService],
        identity: Annotated[CompanyIdentity, Query()],
    ) -> Company:
        return await service.get_one(identity)

    @router.get("/my")
    async def get_my_companies(
        user: Annotated[
            DBUserProtocol,
            Depends(get_authenticated),
        ],
        service: FromDishka[CompanyService],
        pagination: Annotated[OffsetSortedPagination, Query()],
    ) -> OffsetPage[Company]:
        return await service.get_by_user(
            UserCompaniesPagination(
                user_nickname=user.nickname,
                **pagination.model_dump(),
            )
        )

    @router.get(
        "/all",
        dependencies=(Depends(get_authenticated),),
    )
    async def get_all_companies(
        service: FromDishka[CompanyService],
        pagination: Annotated[AllCompaniesPagination, Query()],
    ) -> CursorPage[Company]:
        return await service.get_all(
            CursorSortedPagination(**pagination.model_dump())
        )

    countries: tuple[
        tuple[
            Country,
            type[CompanyAPIClient[CompanyIdentity[str]]],
            type[CompanyIdentity[str]],
        ]
    ] = (
        (
            Country.RUSSIAN_FEDERATION,
            RussianCompanyLegalsAPIFetcher,
            RussianCompanyIdentity,
        ),
    )

    for country, APIClient, Company in countries:

        @router.post(
            f"/create/{country}",
            status_code=HTTPStatus.HTTP_204_NO_CONTENT,
            dependencies=(Depends(get_authenticated),),
        )
        async def create(
            service: FromDishka[CompanyService],
            identity: Company,
        ) -> None:
            await service.create(
                identity,
                APIClient,
            )

    return router
