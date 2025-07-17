from typing import Any

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter


class DishkaRouter(APIRouter):
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs, route_class=DishkaRoute)
