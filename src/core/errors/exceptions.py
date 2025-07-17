class DBConnError(ConnectionError):
    def __init__(self, msg: str = "Internal error.") -> None:
        super().__init__(msg)


class ExternalAPIError(Exception):
    def __init__(self, msg: str = "External service error.") -> None:
        super().__init__(msg)
