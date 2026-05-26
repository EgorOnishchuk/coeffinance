from functools import partial

from httpx import RequestError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from src.core.infrastructure.api_sessions import (
    Sessionmaker,
    TempServerError,
)

backoff = partial(
    wait_random_exponential,
    min=2,
    max=32,
)

core_retry = partial(
    retry,
    stop=stop_after_attempt(3),
    wait=backoff(),
    reraise=True,
)

http_retry = partial(
    core_retry,
    retry=retry_if_exception_type(
        (
            RequestError,
            TempServerError,
        )
    ),
    wait=Sessionmaker.wait_retry_after,
)
