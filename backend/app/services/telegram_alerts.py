from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AlertDraft:
    incident_id: str
    text: str
    status: str
    external_dispatch: str = "not-attempted"


class TelegramAlertService:
    """Safe alert contract. Live delivery is deliberately unavailable in this release."""

    def __init__(self, *, simulation_only: bool | None = None):
        self.simulation_only = simulation_only if simulation_only is not None else os.getenv("TELEGRAM_SIMULATION_ONLY", "true").casefold() == "true"
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

    def draft(self, incident_id: str, text: str) -> AlertDraft:
        if not incident_id or len(incident_id) > 120:
            raise ValueError("incident_id is invalid")
        if not text or len(text) > 2000:
            raise ValueError("alert text is invalid")
        return AlertDraft(incident_id, text, "draft", "not-attempted")

    def send(self, draft: AlertDraft, *, human_approved: bool = False) -> AlertDraft:
        if self.simulation_only or not self.bot_token or not human_approved:
            return AlertDraft(draft.incident_id, draft.text, "blocked_pending_approval", "not-attempted")
        raise RuntimeError("live Telegram delivery is not implemented in the safe release")
