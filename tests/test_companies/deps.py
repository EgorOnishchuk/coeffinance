# mypy: disable-error-code="attr-defined"
# pyright: reportAttributeAccessIssue=false
# Mocks are not supported: https://github.com/python/mypy/issues/1188, https://github.com/microsoft/pyright/discussions/5311.

from unittest.mock import create_autospec

from dishka import provide

from src.companies.service import CompanyService
from src.core.deps.base import BaseProvider
from tests.test_companies.factories import (
    CompanyBaseCursorPageFactory,
    CompanyBaseOffsetPageFactory,
)


class CompanyServiceMockProvider(BaseProvider):
    @provide(override=True)
    def get_service(
        self,
    ) -> CompanyService:
        service: CompanyService = create_autospec(CompanyService, instance=True)

        service.get_by_user.return_value = CompanyBaseOffsetPageFactory.build()
        service.get_all.return_value = CompanyBaseCursorPageFactory.build()

        return service
