from __future__ import annotations

import re
from functools import total_ordering
from statistics import mean
from typing import Annotated, Any, Literal, Self

from pydantic import AfterValidator, Field, field_validator
from pydantic_core import PydanticCustomError

from src.core.validators import (
    CoreValidator,
    CursorSortedPagination,
    NonEmptyStr,
    OffsetSortedPagination,
)
from src.reports.schemas import Report
from src.users.schemas import Nickname, User


@total_ordering
class Company(CoreValidator):
    name: Name
    brn: BRN
    country: Country

    reports: Annotated[set[Report], Field(init=False)] = set()
    users: Annotated[set[User], Field(init=False)] = set()

    @property
    def score(self) -> float:
        return mean(report.score for report in self.reports)

    def __gt__(self, other: Self) -> bool:
        return self.name > other.name

    def __eq__(self, other: Self) -> bool:
        return all(
            (
                self.brn == other.brn,
                self.country == other.country,
            )
        )


class CompanyLegals(CoreValidator):
    name: Name
    brn: BRN
    country: Country


class CompanyIdentity(CoreValidator):
    brn: BRN
    country: Country


class CompanyBRN(CoreValidator):
    brn: BRN


class RussianCompanyBRN(CompanyBRN):
    brn: Annotated[
        BRN,
        Field(
            pattern=re.compile(
                r"^(?P<type>[15])(?P<year>\d{2})(?P<region>(0[1-9]|[1-9]\d))"
                r"(?P<inspectorate>(0[1-9]|[1-9]\d))(?P<entity>\d{5})"
                r"(?P<checksum>\d)$"
            ),
            description="Primary State Registration Number (PSRN)",
        ),]

    @field_validator("brn")
    @classmethod
    def verify_checksum(cls, brn: str) -> str:
        """
        http://pravo.gov.ru/proxy/ips/?savertf=&nd=102460309
        """
        checksum = brn[-1]

        if int(brn[:-1]) % 11 % 10 != int(checksum):
            raise PydanticCustomError(
                "checksum_error",
                "Input should match checksum",
            )

        return brn


class UserCompaniesPagination(OffsetSortedPagination):
    user_nickname: Nickname


Name = Annotated[NonEmptyStr, Field(max_length=300)]
BRN = Annotated[NonEmptyStr, Field(max_length=100)]
type Country = Literal[
    "ABW",
    "AFG",
    "AGO",
    "AIA",
    "ALA",
    "ALB",
    "AND",
    "ARE",
    "ARG",
    "ARM",
    "ASM",
    "ATA",
    "ATF",
    "ATG",
    "AUS",
    "AUT",
    "AZE",
    "BDI",
    "BEL",
    "BEN",
    "BES",
    "BFA",
    "BGD",
    "BGR",
    "BHR",
    "BHS",
    "BIH",
    "BLM",
    "BLR",
    "BLZ",
    "BMU",
    "BOL",
    "BRA",
    "BRB",
    "BRN",
    "BTN",
    "BVT",
    "BWA",
    "CAF",
    "CAN",
    "CCK",
    "CHE",
    "CHL",
    "CHN",
    "CIV",
    "CMR",
    "COD",
    "COG",
    "COK",
    "COL",
    "COM",
    "CPV",
    "CRI",
    "CUB",
    "CUW",
    "CXR",
    "CYM",
    "CYP",
    "CZE",
    "DEU",
    "DJI",
    "DMA",
    "DNK",
    "DOM",
    "DZA",
    "ECU",
    "EGY",
    "ERI",
    "ESH",
    "ESP",
    "EST",
    "ETH",
    "FIN",
    "FJI",
    "FLK",
    "FRA",
    "FRO",
    "FSM",
    "GAB",
    "GBR",
    "GEO",
    "GGY",
    "GHA",
    "GIB",
    "GIN",
    "GLP",
    "GMB",
    "GNB",
    "GNQ",
    "GRC",
    "GRD",
    "GRL",
    "GTM",
    "GUF",
    "GUM",
    "GUY",
    "HKG",
    "HMD",
    "HND",
    "HRV",
    "HTI",
    "HUN",
    "IDN",
    "IMN",
    "IND",
    "IOT",
    "IRL",
    "IRN",
    "IRQ",
    "ISL",
    "ISR",
    "ITA",
    "JAM",
    "JEY",
    "JOR",
    "JPN",
    "KAZ",
    "KEN",
    "KGZ",
    "KHM",
    "KIR",
    "KNA",
    "KOR",
    "KWT",
    "LAO",
    "LBN",
    "LBR",
    "LBY",
    "LCA",
    "LIE",
    "LKA",
    "LSO",
    "LTU",
    "LUX",
    "LVA",
    "MAC",
    "MAF",
    "MAR",
    "MCO",
    "MDA",
    "MDG",
    "MDV",
    "MEX",
    "MHL",
    "MKD",
    "MLI",
    "MLT",
    "MMR",
    "MNE",
    "MNG",
    "MNP",
    "MOZ",
    "MRT",
    "MSR",
    "MTQ",
    "MUS",
    "MWI",
    "MYS",
    "MYT",
    "NAM",
    "NCL",
    "NER",
    "NFK",
    "NGA",
    "NIC",
    "NIU",
    "NLD",
    "NOR",
    "NPL",
    "NRU",
    "NZL",
    "OMN",
    "PAK",
    "PAN",
    "PCN",
    "PER",
    "PHL",
    "PLW",
    "PNG",
    "POL",
    "PRI",
    "PRK",
    "PRT",
    "PRY",
    "PSE",
    "PYF",
    "QAT",
    "REU",
    "ROU",
    "RUS",
    "RWA",
    "SAU",
    "SDN",
    "SEN",
    "SGP",
    "SGS",
    "SHN",
    "SJM",
    "SLB",
    "SLE",
    "SLV",
    "SMR",
    "SOM",
    "SPM",
    "SRB",
    "SSD",
    "STP",
    "SUR",
    "SVK",
    "SVN",
    "SWE",
    "SWZ",
    "SXM",
    "SYC",
    "SYR",
    "TCA",
    "TCD",
    "TGO",
    "THA",
    "TJK",
    "TKL",
    "TKM",
    "TLS",
    "TON",
    "TTO",
    "TUN",
    "TUR",
    "TUV",
    "TWN",
    "TZA",
    "UGA",
    "UKR",
    "UMI",
    "URY",
    "USA",
    "UZB",
    "VAT",
    "VCT",
    "VEN",
    "VGB",
    "VIR",
    "VNM",
    "VUT",
    "WLF",
    "WSM",
    "YEM",
    "ZAF",
    "ZMB",
    "ZWE",
]
