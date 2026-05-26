from typing import Any, cast


def downcast[Target](*, source: Any, target: type[Target]) -> Target:
    source.__class__ = target
    return cast(target, source)
