# """
# =============================================================================
# backend/api/routes/report.py — DAILY REPORT ENDPOINTS
# =============================================================================
# ENDPOINTS:
#   POST /report/daily   — End of day report Slack pe bhejo
#   GET  /report/status  — Aaj ka data dekho
#   POST /report/reset   — Nayi din ke liye reset karo

# USAGE:
#   Din ke aakhir mein:
#     curl -X POST http://localhost:8000/report/daily
#   Ya browser: http://localhost:8000/docs → POST /report/daily
# =============================================================================
# """

# from fastapi import APIRouter

# from backend.agent.tools.slack_tool import SlackTool
# from backend.core.config import settings
# from backend.core.logger import get_logger
# from backend.services.activity_tracker import tracker

# logger = get_logger(__name__)
# router = APIRouter(prefix="/report", tags=["Daily Report"])


# @router.post("/daily")
# async def send_daily_report():
#     """End of day report Slack pe bhejo."""
#     data  = tracker.get_report_data()
#     slack = SlackTool()

#     try:
#         await slack.send_daily_report(
#             channel      = settings.default_slack_channel,
#             date         = data["date"],
#             total_prs    = data["total_prs"],
#             merged_prs   = data["merged_prs"],
#             blocked_prs  = data["blocked_prs"],
#             total_pushes = data["total_pushes"],
#             risk_summary = data["risk_summary"],
#             issues_found = data["issues_found"],
#             jira_created = data["jira_created"],
#             contributors = data["contributors"],
#             highlights   = data["highlights"],
#         )
#         logger.info("[Report] Daily report sent")
#         return {"status": "sent", "channel": settings.default_slack_channel, "data": data}

#     except Exception as e:
#         logger.error(f"[Report] Failed: {e}")
#         return {"status": "failed", "error": str(e)}


# @router.get("/status")
# async def get_report_status():
#     """Aaj ka activity data dekho — report bheje bina."""
#     return tracker.get_report_data()


# @router.post("/reset")
# async def reset_daily_data():
#     """Nayi din ke liye data reset karo."""
#     tracker.reset_for_new_day()
#     return {"status": "reset", "message": "Daily tracker reset for new day"}


"""
=============================================================================
app/api/routes/report.py — DAILY REPORT ENDPOINT
=============================================================================
PURPOSE:
  End of day report manually trigger karo ya schedule karo.

ENDPOINTS:
  POST /report/daily    → Abhi report bhejo Slack pe
  GET  /report/status   → Aaj ka data dekho (JSON)
  POST /report/reset    → New day ke liye reset karo

USAGE:
  Manual trigger (end of day):
    curl -X POST http://localhost:8000/report/daily

  Ya Windows Task Scheduler / cron se automatic:
    Raat 6 baje automatically POST /report/daily call karo
=============================================================================
"""

from datetime import datetime

from fastapi import APIRouter

from backend.agent.tools.slack_tool import SlackTool
from backend.core.config import settings
from backend.core.logger import get_logger
from backend.services.activity_tracker import tracker

logger = get_logger(__name__)

router = APIRouter(prefix="/report", tags=["Daily Report"])


@router.post("/daily")
async def send_daily_report():
    """
    End of day report Slack pe bhejo.

    Ye endpoint call karo din ke aakhir mein:
      curl -X POST http://localhost:8000/report/daily

    Ya browser mein: http://localhost:8000/docs → POST /report/daily
    """
    data  = tracker.get_report_data()
    slack = SlackTool()

    try:
        await slack.send_daily_report(
            channel      = settings.default_slack_channel,
            date         = data["date"],
            total_prs    = data["total_prs"],
            merged_prs   = data["merged_prs"],
            blocked_prs  = data["blocked_prs"],
            total_pushes = data["total_pushes"],
            risk_summary = data["risk_summary"],
            issues_found = data["issues_found"],
            jira_created = data["jira_created"],
            contributors = data["contributors"],
            highlights   = data["highlights"],
        )

        logger.info("[Report] Daily report sent to Slack")
        return {
            "status":  "sent",
            "channel": settings.default_slack_channel,
            "data":    data,
        }

    except Exception as e:
        logger.error(f"[Report] Failed to send: {e}")
        return {"status": "failed", "error": str(e)}


@router.get("/status")
async def get_report_status():
    """Aaj ka activity data dekho — report bheje bina."""
    return tracker.get_report_data()


@router.post("/reset")
async def reset_daily_data():
    """
    Nayi din ke liye data reset karo.
    Daily report bhejne ke baad call karo.
    """
    tracker.reset_for_new_day()
    return {"status": "reset", "message": "Daily tracker reset for new day"}