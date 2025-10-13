from abc import abstractmethod
from typing import Any, Final, Protocol


class Logger(Protocol):
    @abstractmethod
    def debug(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def info(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def warning(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def exception(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def critical(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError


UVICORN_LOGGER: Final = "uvicorn.error"
