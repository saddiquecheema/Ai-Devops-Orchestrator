"""
=============================================================================
backend/api/routes/jira.py — JIRA WEBHOOK ROUTER
=============================================================================
Jira se aane wale events receive karo.
ENDPOINT: POST /webhooks/jira
=============================================================================
"""

from fastapi import APIRouter, BackgroundTasks, Request

from backend.agent.graph import run_agent
from backend.core.logger import get_logger
from backend.models.events import EventType, IncomingEvent

logger = get_logger(__name__)
router = APIRouter(prefix="/jira", tags=["Jira Webhooks"])

JIRA_EVENT_MAP: dict[str, EventType] = {
    "jira:issue_created": EventType.JIRA_ISSUE_CREATED,
    "jira:issue_updated": EventType.JIRA_ISSUE_UPDATED,
}


@router.post("", status_code=202)
async def jira_webhook(request: Request, background_tasks: BackgroundTasks):
    """Jira webhook events receive karo."""
    payload    = await request.json()
    event_name = payload.get("webhookEvent", "")

    event_type = JIRA_EVENT_MAP.get(event_name)
    if not event_type:
        return {"status": "ignored", "reason": f"Unhandled: {event_name}"}

    issue  = payload.get("issue", {})
    fields = issue.get("fields", {})

    event = IncomingEvent(
        event_type     = event_type,
        source         = "jira",
        jira_issue_key = issue.get("key"),
        jira_summary   = fields.get("summary"),
        jira_status    = fields.get("status", {}).get("name"),
        raw_payload    = payload,
    )

    background_tasks.add_task(run_agent, event)
    logger.info(f"[Jira Router] Queued: {event.event_type} | {event.jira_issue_key}")
    return {"status": "accepted", "event_type": event.event_type, "issue_key": event.jira_issue_key}
