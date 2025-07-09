from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from src.persons.dependencies import PersonAsyncpgDALDep
from src.reports.service import ReportService


@lru_cache
def get_report_service(person_dal: PersonAsyncpgDALDep) -> ReportService:
    return ReportService(person_dal=person_dal)


ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
