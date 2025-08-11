from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass

from securepasslib import Validator


class PasswordValidator(ABC):
    @staticmethod
    def _is_containing(password: str, related: Iterable[str]) -> bool:
        return any(related in password for related in related)

    @abstractmethod
    def is_strong(self, password: str, related: Iterable[str]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_improvements(self, password: str) -> tuple[str, ...]:
        raise NotImplementedError


@dataclass(slots=True, frozen=True)
class SecurePassLibValidator(PasswordValidator):
    _complexity_validator: Validator

    def is_strong(self, password: str, related: Iterable[str]) -> bool:
        if self._is_containing(password, related):
            return False

        return self._complexity_validator.is_strong(password)

    def get_improvements(self, password: str) -> tuple[str, ...]:
        return (
            *self._complexity_validator.suggest_improvements(password),
            "Do not mention other credentials from any accounts.",
        )
