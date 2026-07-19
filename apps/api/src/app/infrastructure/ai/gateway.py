"""AI Gateway placeholder — no model calls or agent logic.

Future: route to orchestrator, enforce budgets, risk tiers, and approvals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config.settings import AppSettings, get_settings
from app.infrastructure.logging.setup import get_logger
from app.shared.exceptions import AIError

logger = get_logger("app.ai")


@dataclass(slots=True)
class AIGatewayResult:
    """Placeholder response envelope for future agent runs."""

    accepted: bool
    message: str
    task_id: str | None = None
    metadata: dict[str, Any] | None = None


class AIGateway:
    """Entry point for AI plane from the application layer."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    @property
    def writes_enabled(self) -> bool:
        return self._settings.feature_ai_writes_enabled

    async def health(self) -> dict[str, Any]:
        return {
            "status": "placeholder",
            "writes_enabled": self.writes_enabled,
            "ready_for_agents": False,
        }

    async def submit_task(
        self,
        *,
        agent_code: str,
        capability: str,
        payload: dict[str, Any],
    ) -> AIGatewayResult:
        """Reject real work until agents are implemented."""
        logger.info(
            "ai_gateway_submit_rejected",
            agent_code=agent_code,
            capability=capability,
            reason="foundation_placeholder",
        )
        if not self._settings.feature_ai_assistant_enabled if hasattr(self._settings, "feature_ai_assistant_enabled") else True:
            pass
        raise AIError(
            "AI agents are not implemented in the backend foundation phase",
            code="AI_NOT_IMPLEMENTED",
            retryable=False,
            details=[
                {"field": "agent_code", "issue": agent_code},
                {"field": "capability", "issue": capability},
            ],
        )


_gateway: AIGateway | None = None


def get_ai_gateway(settings: AppSettings | None = None) -> AIGateway:
    global _gateway
    if _gateway is None:
        _gateway = AIGateway(settings or get_settings())
    return _gateway
