from fastapi import APIRouter, status

from src.errors import (
    db_conn_response,
    unexpected_exception_response,
    validation_response,
)
from src.persons.schemas import PersonCreate
from src.reports.dependencies import ReportServiceDep
from src.reports.schemas import CustomReport, OfficialReport
from src.reports.service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="An official report retrieval.",
    response_description="An official report is successfully retrieved.",
    responses={**db_conn_response, **unexpected_exception_response},
)
async def get_official_report(report_service: ReportServiceDep) -> OfficialReport:
    """Retrieves and returns a report generated of all stored persons."""
    return await report_service.create_report()


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    summary="A custom report retrieval.",
    response_description="A custom report is successfully retrieved.",
    responses={
        **unexpected_exception_response,
        **validation_response,
    },
)
def get_custom_report(persons: list[PersonCreate]) -> CustomReport:
    """Retrieves and returns a report generated of all supplied persons."""
    return ReportService.create_custom_report(persons)
