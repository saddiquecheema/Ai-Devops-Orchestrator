"""
=============================================================================
backend/agent/nodes/router_node.py — UPDATED ROUTER NODE
=============================================================================
Har GitHub Push aur PR par ab automatic Jira ticket create hoga.
=============================================================================
"""

from backend.agent.state import AgentState
from backend.core.logger import get_logger
from backend.models.events import EventType

logger = get_logger(__name__)

# Routing Table: Saaf suthra aur koi duplicates nahi
ROUTING_TABLE: dict[EventType, str] = {
    # GitHub Events
    EventType.GITHUB_PR_OPENED:    "create_jira_issue", # PR open hone par bhi ab ticket
    EventType.GITHUB_PR_MERGED:    "create_jira_issue", 
    EventType.GITHUB_PR_CLOSED:    "create_jira_issue",
    EventType.GITHUB_PUSH:         "create_jira_issue", # Har Push par ab ticket
    
    # Slack Events
    EventType.SLACK_MESSAGE:       "create_jira_issue",
    EventType.SLACK_COMMAND:       "create_jira_issue",
    
    # Jira Notifications (Inke liye sirf slack notify hoga)
    EventType.JIRA_ISSUE_CREATED:  "notify_slack",
    EventType.JIRA_ISSUE_UPDATED:  "notify_slack",
}

async def router_node(state: AgentState) -> dict:
    """Event type ke mutabiq next node decide karo."""
    event = state["event"]
    
    # Router logic
    next_action = ROUTING_TABLE.get(event.event_type, "handle_error")
    
    logger.info(f"[Router] {event.event_type.value} → {next_action}")
    
    return {"next_action": next_action}