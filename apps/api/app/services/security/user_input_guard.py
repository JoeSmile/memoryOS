"""User-input guard protocol — heuristic + optional ML adapters (EP09 2.8/2.9)."""

from collections.abc import Sequence
from typing import Protocol

from app.services.security.llm_guard_adapter import assert_llm_guard_user_input
from app.services.security.prompt_security import assert_user_input_safe


class UserInputGuard(Protocol):
    def validate(self, content: str) -> None:
        """Raise AppException when input must be rejected before LLM invocation."""


class HeuristicUserInputGuard:
    def validate(self, content: str) -> None:
        assert_user_input_safe(content)


class LlmGuardUserInputGuard:
    def validate(self, content: str) -> None:
        assert_llm_guard_user_input(content)


_DEFAULT_GUARDS: tuple[UserInputGuard, ...] = (
    HeuristicUserInputGuard(),
    LlmGuardUserInputGuard(),
)


def run_user_input_guards(
    content: str,
    guards: Sequence[UserInputGuard] | None = None,
) -> None:
    """Northbound L0 chain: heuristic (2.2) then optional LLM Guard (2.9)."""
    for guard in guards or _DEFAULT_GUARDS:
        guard.validate(content)
