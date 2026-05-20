from __future__ import annotations

from contextlib import suppress
from typing import Any, Protocol


class LangfuseLike(Protocol):  # pragma: no cover - simple protocol
    def trace(
        self, *, name: str, input: Any | None = None, output: Any | None = None, **kwargs: Any
    ) -> Any: ...

    def log(self, *args: Any, **kwargs: Any) -> Any: ...


def emit_trace(
    client: LangfuseLike | None, *, name: str, input: Any | None = None, output: Any | None = None
) -> None:
    """Emit a trace to Langfuse if a compatible client is present."""
    if client is None:
        return

    if hasattr(client, "trace"):
        with suppress(Exception):
            client.trace(name=name, input=input, output=output)
            return

    if hasattr(client, "log"):
        with suppress(Exception):
            client.log(name=name, input=input, output=output)
