from dataclasses import dataclass

from src.persons.data_access_layer import PersonDAL
from src.persons.schemas import PersonCreate
from src.reports.schemas import CustomReport, OfficialReport


@dataclass(kw_only=True, frozen=True, slots=True)
class ReportService:
    person_dal: PersonDAL

    async def create_report(self) -> OfficialReport:
        persons = await self.person_dal.read_all()

        return OfficialReport(persons=persons)

    @staticmethod
    def create_custom_report(persons: list[PersonCreate]) -> CustomReport:
        return CustomReport(persons=persons)
