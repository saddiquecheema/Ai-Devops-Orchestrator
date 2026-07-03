"""
=============================================================================
backend/api/routes/system.py — SYSTEM ENDPOINTS
=============================================================================
ENDPOINTS:
  GET  /health        — Server alive check
  GET  /info          — Config summary (no secrets)
  POST /test/trigger  — Manual agent test (development)
=============================================================================
"""

import time

from fastapi import APIRouter

from backend.agent.graph import run_agent
from backend.core.config import settings
from backend.core.logger import get_logger
from backend.models.events import IncomingEvent

logger = get_logger(__name__)
router = APIRouter(tags=["System"])


@router.get("/health")
async def health_check():
    """Server alive check — load balancers ke liye."""
    return {
        "status":    "healthy",
        "service":   "ai-devops-orchestrator",
        "version":   "1.0.0",
        "timestamp": time.time(),
    }


@router.get("/info")
async def app_info():
    """Config summary — sensitive values mask karke."""
    return {
        "service":          "AI-Driven DevOps Orchestrator",
        "version":          "1.0.0",
        "environment":      settings.app_env,
        "llm_model":        settings.groq_model,
        "jira_project":     settings.jira_project_key,
        "slack_channel":    settings.default_slack_channel,
        "github_token_set": bool(settings.github_token and settings.github_token != "placeholder"),
        "groq_key_set":     bool(settings.groq_api_key  and settings.groq_api_key  != "placeholder"),
        "slack_token_set":  bool(settings.slack_bot_token and settings.slack_bot_token != "placeholder"),
        "jira_token_set":   bool(settings.jira_api_token and settings.jira_api_token != "placeholder"),
    }


@router.post("/test/trigger")
async def manual_trigger(event: IncomingEvent):
    """
    Agent ko manually test karo.
    Development mein use karo — real webhook ke bina.

    Example:
    {
      "event_type": "github.pr.opened",
      "source": "github",
      "repo": "Muinam/bg-removal",
      "pr_number": 1,
      "pr_title": "Add feature",
      "pr_author": "Muinam"
    }
    """
    logger.info(f"[Test Trigger] Manual: {event.event_type}")
    return await run_agent(event)
