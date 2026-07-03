# """
# =============================================================================
# backend/api/routes/github.py — GITHUB WEBHOOK ROUTER (DEVELOPMENT MODE)
# =============================================================================
# """

# import json
# from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Header

# from backend.agent.graph import run_agent
# from backend.core.logger import get_logger
# from backend.models.events import EventType, IncomingEvent
# from backend.utils.security import verify_github_signature

# logger = get_logger(__name__)

# router = APIRouter(prefix="/webhooks", tags=["GitHub Webhooks"])

# # 🚫 DEVELOPMENT NOTE: IGNORE_PATTERNS ko abhi ke liye block nahi kar rahe 
# # taake aap README.md change karke aaram se test kar sakein.

# def _parse_github_event(event_name: str, payload: dict) -> IncomingEvent | None:
#     """Raw GitHub payload → IncomingEvent."""
#     repo = payload.get("repository", {}).get("full_name", "unknown/unknown")

#     if event_name == "pull_request":
#         action = payload.get("action", "")
#         pr = payload.get("pull_request", {})

#         action_map = {
#             "opened":   EventType.GITHUB_PR_OPENED,
#             "reopened": EventType.GITHUB_PR_OPENED,
#             "closed":   EventType.GITHUB_PR_MERGED if pr.get("merged") else EventType.GITHUB_PR_CLOSED,
#         }
#         event_type = action_map.get(action)
#         if not event_type:
#             return None

#         return IncomingEvent(
#             event_type=event_type,
#             source="github",
#             repo=repo,
#             pr_number=pr.get("number"),
#             pr_title=pr.get("title", ""),
#             pr_body=pr.get("body", ""),
#             pr_author=pr.get("user", {}).get("login", "unknown"),
#             branch=pr.get("base", {}).get("ref", ""),
#             raw_payload=payload,
#         )

#     if event_name == "push":
#         branch = payload.get("ref", "").replace("refs/heads/", "")
#         commits = payload.get("commits", [])

#         pusher_name = payload.get("pusher", {}).get("name", "unknown")
#         last_commit_msg = commits[-1].get("message", "").split("\n")[0] if commits else ""

#         return IncomingEvent(
#             event_type=EventType.GITHUB_PUSH,
#             source="github",
#             repo=repo,
#             branch=branch,
#             commit_sha=payload.get("after", ""),
#             pusher=pusher_name,
#             commit_msg=last_commit_msg,
#             raw_payload=payload,
#         )

#     return None


# @router.post("/github", status_code=202)
# async def github_webhook(
#     request: Request, 
#     background_tasks: BackgroundTasks,
#     x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
#     x_github_event: str = Header(..., alias="X-GitHub-Event"),
#     x_github_delivery: str = Header("unknown", alias="X-GitHub-Delivery")
# ):
#     """Webhook Endpoint - Ready for README.md testing."""
#     body = await request.body()

#     # 1. Security Verification
#     if not x_hub_signature_256 or not verify_github_signature(body, x_hub_signature_256):
#         logger.warning(f"[Security] Unauthorized webhook attempt. Delivery: {x_github_delivery}")
#         raise HTTPException(status_code=401, detail="Invalid GitHub webhook signature")

#     try:
#         payload = json.loads(body)
#     except json.JSONDecodeError:
#         raise HTTPException(status_code=400, detail="Invalid JSON payload")

#     logger.info(f"[GitHub Router] Event: {x_github_event} | Delivery: {x_github_delivery[:16]}")

#     # 2. Parsing (Ab README ko ignore nahi karega, seedha pass karega)
#     event = _parse_github_event(x_github_event, payload)
#     if not event:
#         return {"status": "ignored", "reason": f"Event {x_github_event} did not match processing criteria"}

#     # 3. Queue Background Task
#     background_tasks.add_task(run_agent, event)
#     logger.info(f"[GitHub Router] Queued: {event.event_type} | repo={event.repo}")
    
#     return {
#         "status": "accepted", 
#         "event_type": event.event_type, 
#         "repo": event.repo,
#         "delivery_id": x_github_delivery
#     }

"""
=============================================================================
backend/api/routes/github.py — GITHUB WEBHOOK ROUTER (LIVE DASHBOARD ACTIVE)
=============================================================================
"""

import json
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Header

from backend.agent.graph import run_agent
from backend.core.logger import get_logger
from backend.models.events import EventType, IncomingEvent
from backend.utils.security import verify_github_signature
# CRITICAL CONNECTION: Apne main file se global ws_manager import karein
from backend.main import ws_manager 

logger = get_logger(__name__)
router = APIRouter(prefix="/webhooks", tags=["GitHub Webhooks"])

def _parse_github_event(event_name: str, payload: dict) -> IncomingEvent | None:
    """Raw GitHub payload → IncomingEvent."""
    repo = payload.get("repository", {}).get("full_name", "unknown/unknown")

    if event_name == "pull_request":
        action = payload.get("action", "")
        pr = payload.get("pull_request", {})

        action_map = {
            "opened":   EventType.GITHUB_PR_OPENED,
            "reopened": EventType.GITHUB_PR_OPENED,
            "closed":   EventType.GITHUB_PR_MERGED if pr.get("merged") else EventType.GITHUB_PR_CLOSED,
        }
        event_type = action_map.get(action)
        if not event_type:
            return None

        return IncomingEvent(
            event_type=event_type,
            source="github",
            repo=repo,
            pr_number=pr.get("number"),
            pr_title=pr.get("title", ""),
            pr_body=pr.get("body", ""),
            pr_author=pr.get("user", {}).get("login", "unknown"),
            branch=pr.get("base", {}).get("ref", ""),
            raw_payload=payload,
        )

    if event_name == "push":
        branch = payload.get("ref", "").replace("refs/heads/", "")
        commits = payload.get("commits", [])

        pusher_name = payload.get("pusher", {}).get("name", "unknown")
        last_commit_msg = commits[-1].get("message", "").split("\n")[0] if commits else ""

        return IncomingEvent(
            event_type=EventType.GITHUB_PUSH,
            source="github",
            repo=repo,
            branch=branch,
            commit_sha=payload.get("after", ""),
            pusher=pusher_name,
            commit_msg=last_commit_msg,
            raw_payload=payload,
        )

    return None


@router.post("/github", status_code=202)
async def github_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_github_delivery: str = Header("unknown", alias="X-GitHub-Delivery")
):
    """Webhook Endpoint - Emitting live signals to WebSocket Panel."""
    body = await request.body()

    # 1. Security Verification
    if not x_hub_signature_256 or not verify_github_signature(body, x_hub_signature_256):
        logger.warning(f"[Security] Unauthorized webhook attempt. Delivery: {x_github_delivery}")
        raise HTTPException(status_code=401, detail="Invalid GitHub webhook signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    logger.info(f"[GitHub Router] Event: {x_github_event} | Delivery: {x_github_delivery[:16]}")

    # 2. Parsing Event
    event = _parse_github_event(x_github_event, payload)
    if not event:
        return {"status": "ignored", "reason": f"Event {x_github_event} did not match processing criteria"}

    # =========================================================================
    # LIVE UPDATE 1: Jaise hi payload parse ho, frontend ko immediate notify karo
    # =========================================================================
    if event.event_type == EventType.GITHUB_PUSH:
        await ws_manager.broadcast({
            "type": "webhook",
            "message": f"Git Push Event received for <b>{event.repo}</b> on branch <span class='text-indigo-400 font-mono'>{event.branch}</span>."
        })
        await ws_manager.broadcast({
            "type": "agent_log",
            "message": f"Pusher: <b>@{event.pusher}</b> | Commit Message: <i>\"{event.commit_msg}\"</i>"
        })
    elif event.event_type in [EventType.GITHUB_PR_OPENED, EventType.GITHUB_PR_CLOSED, EventType.GITHUB_PR_MERGED]:
        await ws_manager.broadcast({
            "type": "webhook",
            "message": f"Pull Request Event (<b>{x_github_event}</b>) captured for <b>{event.repo}</b>."
        })

    # =========================================================================
    # LIVE UPDATE 2: AI Agent active hone ka log stream bhejein
    # =========================================================================
    await ws_manager.broadcast({
        "type": "agent_log",
        "message": "Initializing <b>LangGraph Orchestrator</b> workflow thread..."
    })

    # 3. Queue Background Task (LangGraph Execution)
    background_tasks.add_task(run_agent, event)
    logger.info(f"[GitHub Router] Queued: {event.event_type} | repo={event.repo}")
    
    return {
        "status": "accepted", 
        "event_type": event.event_type, 
        "repo": event.repo,
        "delivery_id": x_github_delivery
    }