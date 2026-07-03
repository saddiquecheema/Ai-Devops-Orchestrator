# """
# =============================================================================
# backend/agent/nodes/finalize_node.py — FINALIZE + ERROR HANDLER NODES
# =============================================================================
# """

# from backend.agent.state import AgentState
# from backend.agent.tools.slack_tool import SlackTool
# from backend.core.config import settings
# from backend.core.logger import get_logger
# from backend.core.websocket import ws_manager
# from backend.models.responses import OrchestratorResponse
# from backend.core.database import SessionLocal
# from backend.models.stats import Stats, ActivityLog

# logger = get_logger(__name__)


# def _increment_stat(key: str):
#     """Stat count database mein barha do."""
#     db = SessionLocal()
#     try:
#         stat = db.query(Stats).filter(Stats.key == key).first()
#         if not stat:
#             stat = Stats(key=key, count=0)
#             db.add(stat)
#         stat.count += 1
#         db.commit()
#     except Exception as e:
#         logger.error(f"[Finalize] Stat increment failed: {e}")
#     finally:
#         db.close()


# def _save_activity(event_type: str, message: str, priority: str = None):
#     """Activity log mein save karo."""
#     db = SessionLocal()
#     try:
#         log = ActivityLog(
#             event_type=event_type,
#             message=message,
#             priority=priority
#         )
#         db.add(log)
#         db.commit()
#     except Exception as e:
#         logger.error(f"[Finalize] Activity log failed: {e}")
#     finally:
#         db.close()


# async def finalize_node(state: AgentState) -> dict:
#     """Final response banao, stats save karo, broadcast karo."""
#     actions = state.get("actions_taken", [])
#     errors  = state.get("errors", [])
#     event   = state["event"]
#     success = len(errors) == 0

#     # ✅ Stats database mein save karo
#     for action in actions:
#         if "jira_issue_created" in action:
#             _increment_stat("jira_tickets")
#             ticket_key = action.split(":")[-1] if ":" in action else "N/A"
#             _save_activity("ticket", f"Jira {ticket_key}: Auto-created from pipeline", "low")

#         elif "slack" in action:
#             _increment_stat("slack_alerts")
#             _save_activity("slack", f"Slack notification sent: {event.event_type.value}", None)

#     # Git event bhi save karo
#     if hasattr(event, 'repo') and event.repo:
#         _increment_stat("git_events")
#         branch = getattr(event, 'branch', 'main')
#         _save_activity("git", f"Git Push Event received for {event.repo} on branch {branch}", None)

#     # WebSocket broadcast
#     await ws_manager.broadcast({
#         "type": "pipeline_complete",
#         "success": success,
#         "pr_number": getattr(event, "pr_number", "N/A"),
#         "message": "✅ Pipeline Finished Successfully" if success else "❌ Pipeline Finished with Errors",
#         "actions": actions[-3:]
#     })

#     response = OrchestratorResponse(
#         success       = success,
#         event_type    = event.event_type,
#         actions_taken = actions,
#         errors        = errors,
#     )

#     logger.info(
#         f"[Finalize] Done | success={success} | "
#         f"actions={actions} | errors={errors}"
#     )

#     return {"final_response": response}


# async def error_handler_node(state: AgentState) -> dict:
#     """Error handler node."""
#     errors  = state.get("errors", [])
#     actions = state.get("actions_taken", [])
#     event   = state["event"]

#     await ws_manager.broadcast({
#         "type": "pipeline_error",
#         "message": f"🚨 Pipeline Failed: {errors[0] if errors else 'Unknown Error'}",
#         "pr_number": getattr(event, "pr_number", "N/A")
#     })

#     logger.error(f"[Error Handler] Errors: {errors}")

#     try:
#         slack = SlackTool()
#         short_msg = errors[0][:80] if errors else "Unknown error"
#         detail    = " | ".join(errors) if errors else "No details available"
#         await slack.send_error_alert(
#             channel    = settings.default_slack_channel,
#             error_type = "SystemError",
#             short_msg  = short_msg,
#             detail     = detail,
#             source     = f"Agent Pipeline — {event.event_type}",
#         )
#     except Exception as slack_err:
#         logger.error(f"[Error Handler] Could not send Slack alert: {slack_err}")

#     return {
#         "final_response": OrchestratorResponse(
#             success       = False,
#             event_type    = event.event_type,
#             actions_taken = actions,
#             errors        = errors,
#         )
#     }

from backend.agent.state import AgentState
from backend.agent.tools.slack_tool import SlackTool
from backend.core.config import settings
from backend.core.logger import get_logger
from backend.core.websocket import ws_manager
from backend.models.responses import OrchestratorResponse
from backend.core.database import SessionLocal
from backend.models.stats import Stats, ActivityLog

logger = get_logger(__name__)


def _increment_stat(project_id: int, key: str):
    if not project_id:
        return
    db = SessionLocal()
    try:
        stat = db.query(Stats).filter(
            Stats.project_id == project_id,
            Stats.key == key
        ).first()
        if not stat:
            stat = Stats(project_id=project_id, key=key, count=0)
            db.add(stat)
        stat.count += 1
        db.commit()
    except Exception as e:
        logger.error(f"[Finalize] Stat increment failed: {e}")
    finally:
        db.close()


def _save_activity(project_id: int, event_type: str, message: str, priority: str = None):
    db = SessionLocal()
    try:
        log = ActivityLog(
            project_id=project_id,
            event_type=event_type,
            message=message,
            priority=priority
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.error(f"[Finalize] Activity log failed: {e}")
    finally:
        db.close()


async def finalize_node(state: AgentState) -> dict:
    actions = state.get("actions_taken", [])
    errors  = state.get("errors", [])
    event   = state["event"]
    success = len(errors) == 0

    # Get project_id from event if available
    project_id = getattr(event, "project_id", None)

    for action in actions:
        if "jira_issue_created" in action:
            _increment_stat(project_id, "jira_tickets")
            ticket_key = action.split(":")[-1] if ":" in action else "N/A"
            _save_activity(project_id, "ticket", f"Jira {ticket_key}: Auto-created from pipeline", "low")
        elif "slack" in action:
            _increment_stat(project_id, "slack_alerts")
            _save_activity(project_id, "slack", f"Slack notification sent: {event.event_type.value}")

    if hasattr(event, 'repo') and event.repo:
        _increment_stat(project_id, "git_events")
        branch = getattr(event, 'branch', 'main')
        _save_activity(project_id, "git", f"Git Push Event received for {event.repo} on branch {branch}")

    await ws_manager.broadcast({
        "type": "pipeline_complete",
        "success": success,
        "pr_number": getattr(event, "pr_number", "N/A"),
        "message": "✅ Pipeline Finished Successfully" if success else "❌ Pipeline Finished with Errors",
        "actions": actions[-3:]
    })

    response = OrchestratorResponse(
        success       = success,
        event_type    = event.event_type,
        actions_taken = actions,
        errors        = errors,
    )

    logger.info(f"[Finalize] Done | success={success} | actions={actions} | errors={errors}")
    return {"final_response": response}


async def error_handler_node(state: AgentState) -> dict:
    errors  = state.get("errors", [])
    actions = state.get("actions_taken", [])
    event   = state["event"]

    await ws_manager.broadcast({
        "type": "pipeline_error",
        "message": f"🚨 Pipeline Failed: {errors[0] if errors else 'Unknown Error'}",
        "pr_number": getattr(event, "pr_number", "N/A")
    })

    logger.error(f"[Error Handler] Errors: {errors}")

    try:
        slack = SlackTool()
        short_msg = errors[0][:80] if errors else "Unknown error"
        detail    = " | ".join(errors) if errors else "No details"
        await slack.send_error_alert(
            channel    = settings.default_slack_channel,
            error_type = "SystemError",
            short_msg  = short_msg,
            detail     = detail,
            source     = f"Agent Pipeline — {event.event_type}",
        )
    except Exception as slack_err:
        logger.error(f"[Error Handler] Slack alert failed: {slack_err}")

    return {
        "final_response": OrchestratorResponse(
            success       = False,
            event_type    = event.event_type,
            actions_taken = actions,
            errors        = errors,
        )
    }