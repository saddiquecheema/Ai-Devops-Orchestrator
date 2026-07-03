"""
=============================================================================
backend/api/routes/slack.py — SLACK WEBHOOK ROUTER
=============================================================================
Slack Events API receive karo.
ENDPOINT: POST /webhooks/slack

TRIGGER KEYWORDS: bug: | issue: | task: | create: | ticket:
URL VERIFICATION: Slack ka challenge automatically handle hota hai.
=============================================================================
"""

import json

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from backend.agent.graph import run_agent
from backend.core.logger import get_logger
from backend.models.events import EventType, IncomingEvent
from backend.utils.security import verify_slack_signature

logger = get_logger(__name__)
router = APIRouter(prefix="/webhooks/slack", tags=["Slack Webhooks"])

TRIGGER_KEYWORDS = ("bug:", "issue:", "task:", "create:", "ticket:")


@router.post("", status_code=202)
async def slack_webhook(request: Request, background_tasks: BackgroundTasks):
    """Slack Events API events receive karo."""
    body      = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    signature = request.headers.get("X-Slack-Signature")

    if not verify_slack_signature(body, timestamp, signature):
        raise HTTPException(status_code=401, detail="Invalid Slack webhook signature")

    payload      = json.loads(body)
    payload_type = payload.get("type", "")

    # URL verification challenge
    if payload_type == "url_verification":
        logger.info("[Slack Router] URL verification challenge")
        return {"challenge": payload["challenge"]}

    if payload_type != "event_callback":
        return {"status": "ignored"}

    slack_event = payload.get("event", {})
    event_type  = slack_event.get("type", "")

    if event_type == "message":
        if slack_event.get("bot_id") or slack_event.get("subtype"):
            return {"status": "ignored", "reason": "bot or subtype message"}

        text = slack_event.get("text", "").strip().lower()
        if not any(text.startswith(kw) for kw in TRIGGER_KEYWORDS):
            return {"status": "ignored", "reason": "no trigger keyword"}

        event = IncomingEvent(
            event_type    = EventType.SLACK_MESSAGE,
            source        = "slack",
            slack_channel = slack_event.get("channel"),
            slack_user    = slack_event.get("user"),
            slack_text    = slack_event.get("text"),
            raw_payload   = payload,
        )

        background_tasks.add_task(run_agent, event)
        logger.info(f"[Slack Router] Queued | channel={event.slack_channel}")
        return {"status": "accepted", "event_type": event.event_type}

    return {"status": "ignored"}
