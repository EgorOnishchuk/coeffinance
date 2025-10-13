import re
from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pycountry import countries
from pydantic import AwareDatetime, Field, field_validator
from pydantic_extra_types.country import CountryShortName

from src.analytics.schemas import Analytics
from src.core.schemas import (
    CursorSortingSearch,
    NonEmptyStr,
    OffsetSortingSearch,
    Schema,
)
from src.users.schemas import Nickname, UserRead

BaseBRN = Annotated[NonEmptyStr, Field(max_length=100)]
BaseName = Annotated[NonEmptyStr, Field(max_length=300)]
Countries = StrEnum(  # type: ignore[misc] # A MyPy limitation to determine dynamically generated values: https://github.com/python/mypy/issues/4865#issuecomment-592560696.
    "Countries",
    {country_.alpha_2: country_.name for country_ in countries},  # pyright: ignore[reportAttributeAccessIssue] # Specifics of the lib design.
)


class RussianBRN(Schema):
    brn: Annotated[
        NonEmptyStr,
        Field(
            pattern=re.compile(
                r"^(?P<type>[15])(?P<year>\d{2})(?P<region>(0[1-9]|[1-9]\d))"
                r"(?P<inspectorate>(0[1-9]|[1-9]\d))(?P<entity>\d{5})"
                r"(?P<checksum>\d)$"
            ),
            description="Is called a Primary State Registration Number (PSRN).",
        ),
    ]

    @field_validator("brn", mode="after")
    @classmethod
    def verify_checksum(cls, brn: str) -> str:
        """
        The algorithm is described in «Приказ Минфина России от 30.10.2017
        № 165н "Об утверждении Порядка ведения Единого государственного реестра
        юридических лиц и Единого государственного реестра индивидуальных
        предпринимателей, внесения исправлений в сведения, включенные в записи
        Единого государственного реестра юридических лиц и Единого
        государственного реестра индивидуальных предпринимателей на электронных
        носителях, не соответствующие сведениям, содержащимся в документах, на
        основании которых внесены такие записи (исправление технической ошибки),
        и о признании утратившим силу приказа Министерства финансов Российской
        Федерации от 18 февраля 2015 г. № 25н"».
        """
        checksum = brn[-1]
        if int(brn[:-1]) % 11 % 10 != int(checksum):
            raise ValueError(f"Checksum {checksum} is invalid")
        return brn


class CompanyFetch(Schema):
    brn: BaseBRN


class RussianCompanyFetch(RussianBRN, CompanyFetch):
    pass


class CompanyCreate(Schema):
    name: BaseName
    brn: BaseBRN
    country: CountryShortName


class RussianCompanyCreate(RussianBRN, CompanyCreate):
    country: CountryShortName = CountryShortName("Russian Federation")


class CompanyRead(Schema):
    name: BaseName
    brn: BaseBRN
    country: CountryShortName
    score: Annotated[Decimal | None, Field(ge=0, le=100)] = None
    created_at: AwareDatetime

    analytics: list[Analytics]
    users: list[UserRead]


class CompanySearch(Schema):
    brn: BaseBRN
    country: CountryShortName


class UserCompaniesSearch(OffsetSortingSearch):
    user_nickname: Nickname


class AllCompaniesSearch(CursorSortingSearch):
    @field_validator("next_page", mode="after")
    @classmethod
    def empty_to_none(cls, next_page: str) -> str | None:
        """
        None cannot be sent via query params. (See RFC 3986 for details)
        """
        return next_page or None
