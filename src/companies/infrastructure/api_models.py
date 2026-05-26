"""
Based on auto-generation from https://api-fns.ru/api_help#section_poisk examples
using datamodel-code-generator.
"""

from collections.abc import Sequence
from typing import Annotated

from pydantic import Field, NonNegativeInt

from src.companies.schemas import Name, RussianCompanyBRN
from src.core.validators import CoreValidator


class APIFNSEntity(CoreValidator):
    brn: Annotated[RussianCompanyBRN, Field(validation_alias="ОГРН")]
    name: Annotated[Name, Field(validation_alias="НаимПолнЮЛ")]


class APIFNSItem(CoreValidator):
    entity: Annotated[APIFNSEntity, Field(validation_alias="ЮЛ")]


class APIFNSLegalEntities(CoreValidator):
    items: Sequence[APIFNSItem]
    count: NonNegativeInt
