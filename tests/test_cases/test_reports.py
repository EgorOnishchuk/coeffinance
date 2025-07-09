from datetime import date

import pytest
from asyncpg import Connection

from src.persons.data_access_layer import PersonAsyncpgDAL
from src.persons.schemas import PersonCreate
from src.reports.service import ReportService
from tests.test_cases.base import TestUnit


class TestReportService(TestUnit):
    service_cls = ReportService
    dal_cls = PersonAsyncpgDAL

    @pytest.fixture(autouse=True)
    def set_service(self, conn_: Connection) -> None:
        self.service = self.service_cls(person_dal=self.dal_cls(_conn=conn_))

    @pytest.fixture
    def persons(self) -> list[PersonCreate]:
        return [
            PersonCreate(
                first_name="Rosa",
                last_name="Sanford",
                gender="female",
                birthdate=date(1999, 3, 16),
            ),
            PersonCreate(
                first_name="John",
                last_name="Doe",
                gender="male",
                birthdate=date(2001, 1, 1),
            ),
        ]

    def test_create_custom(self, persons: list[PersonCreate]) -> None:
        report = self.service.create_custom_report(persons=persons)

        for person in persons:
            assert person in report.persons
