from src.core.errors import BusinessError


class NormalRangeError(BusinessError):
    pass


class EmptyRatiosError(BusinessError):
    pass


class TotalWeightError(BusinessError):
    pass
