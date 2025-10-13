from collections.abc import Iterable
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any

from src.core.schemas import Schema


@dataclass(kw_only=True, slots=True, frozen=True)
class ResponseEditor:
    """
    Intended for one-time and targeted editing of the docs where high-level
    tools cannot be used. For example, libs that provide ready-made boilerplate
    routers may hardcode their routes' metadata.
    """

    _responses: Iterable[dict[int, dict[str, Any]]]

    def override_error(
        self,
        *,
        error: type[Schema],
        code: HTTPStatus,
    ) -> None:
        for response in self._responses:
            (response.get(int(code), {}))["model"] = error

    def remove_examples(self) -> None:
        for response in self._responses:
            for status in response.values():
                status.get("content", {}).get("application/json", {}).pop(
                    "examples", None
                )
