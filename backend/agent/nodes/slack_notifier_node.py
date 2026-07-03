# """
# =============================================================================
# backend/agent/nodes/slack_notifier_node.py — SLACK NOTIFIER NODE
# =============================================================================
# Har event ke liye proper Slack notification.
# LLM use NAHI karta — fast aur cheap.

# PUSH notification mein:
#   Developer naam, exact time, branch, commit SHA, commit message
# =============================================================================
# """

# import time

# from backend.agent.state import AgentState
# from backend.agent.tools.slack_tool import SlackTool
# from backend.core.config import settings
# from backend.core.logger import get_logger
# from backend.models.events import EventType, IncomingEvent
# from backend.main import ws_manager
# logger = get_logger(__name__)


# def _format_push_blocks(event: IncomingEvent) -> list[dict]:
#     """Push event card — developer + time + commit info."""
#     pusher     = event.pusher     or event.pr_author or "Unknown Developer"
#     commit_sha = (event.commit_sha or "")[:8] or "N/A"
#     branch     = event.branch     or "N/A"
#     repo       = event.repo       or "N/A"
#     commit_msg = event.commit_msg or "No commit message"
#     timestamp  = int(event.received_at or time.time())

#     commit_url = f"https://github.com/{repo}/commit/{event.commit_sha}" if event.repo and event.commit_sha else "#"
#     repo_url   = f"https://github.com/{repo}" if repo != "N/A" else "#"

#     return [
#         {
#             "type": "header",
#             "text": {"type": "plain_text", "text": "Code Push Detected", "emoji": False},
#         },
#         {
#             "type": "section",
#             "fields": [
#                 {"type": "mrkdwn", "text": f"*Developer*\n`{pusher}`"},
#                 {"type": "mrkdwn", "text": f"*Time*\n<!date^{timestamp}^{{date_short_pretty}} at {{time}}|just now>"},
#             ],
#         },
#         {"type": "divider"},
#         {
#             "type": "section",
#             "fields": [
#                 {"type": "mrkdwn", "text": f"*Repository*\n<{repo_url}|`{repo}`>"},
#                 {"type": "mrkdwn", "text": f"*Branch*\n`{branch}`"},
#             ],
#         },
#         {
#             "type": "section",
#             "fields": [
#                 {"type": "mrkdwn", "text": f"*Commit*\n<{commit_url}|`{commit_sha}`>"},
#                 {"type": "mrkdwn", "text": f"*Message*\n{commit_msg[:80]}"},
#             ],
#         },
#         {"type": "divider"},
#         {
#             "type": "context",
#             "elements": [{"type": "mrkdwn", "text": f"DevOps Orchestrator  |  Push Monitor  |  `{repo}`"}],
#         },
#     ]


# def _format_pr_merged_blocks(event: IncomingEvent) -> list[dict]:
#     """PR merge notification card."""
#     pr_url    = f"https://github.com/{event.repo}/pull/{event.pr_number}" if event.repo and event.pr_number else "#"
#     timestamp = int(event.received_at or time.time())

#     return [
#         {
#             "type": "header",
#             "text": {"type": "plain_text", "text": f"Pull Request Merged — PR #{event.pr_number or 'N/A'}", "emoji": False},
#         },
#         {
#             "type": "section",
#             "text": {"type": "mrkdwn", "text": f"*<{pr_url}|{event.pr_title or 'Untitled PR'}>*"},
#         },
#         {
#             "type": "section",
#             "fields": [
#                 {"type": "mrkdwn", "text": f"*Merged By*\n`{event.pr_author or 'Unknown'}`"},
#                 {"type": "mrkdwn", "text": f"*Time*\n<!date^{timestamp}^{{date_short_pretty}} at {{time}}|just now>"},
#                 {"type": "mrkdwn", "text": f"*Repository*\n`{event.repo or 'N/A'}`"},
#                 {"type": "mrkdwn", "text": f"*Target Branch*\n`{event.branch or 'main'}`"},
#             ],
#         },
#         {"type": "divider"},
#         {
#             "type": "context",
#             "elements": [{"type": "mrkdwn", "text": f"DevOps Orchestrator  |  `{event.repo or 'N/A'}`"}],
#         },
#     ]
# async def _broadcast_slack_card(title: str, event: IncomingEvent):
#     """Frontend ke liye Slack card broadcast karne ka helper."""
#     await ws_manager.broadcast({
#         "type": "slack_card",
#         "title": title,
#         "details": {
#             "pusher": event.pusher or "N/A",
#             "branch": event.branch or "N/A",
#             "repo": event.repo or "N/A",
#             "message": event.commit_msg or "No message"
#         },
#         "blocks": _format_push_blocks(event) 
#     })

# async def notify_slack_node(state: AgentState) -> dict:
#     """Event type ke hisaab se Slack card bhejo."""
#     event   = state["event"]
#     actions = list(state.get("actions_taken", []))
#     errors  = list(state.get("errors", []))
#     slack   = SlackTool()

#     # Notification ka description taiyaar karo
#     notification_text = f"Event: {event.event_type} handled"

#     try:
#         if event.event_type == EventType.GITHUB_PUSH:
#             await slack.send_message(
#                 channel=settings.default_slack_channel,
#                 text=f"Code push by {event.pusher} to {event.branch}",
#                 blocks=_format_push_blocks(event),
#             )
#             notification_text = "Code Push Notification Sent"
#             await _broadcast_slack_card("Code Push Detected", event)

#         elif event.event_type == EventType.GITHUB_PR_MERGED:
#             await slack.send_message(
#                 channel=settings.default_slack_channel,
#                 text=f"PR #{event.pr_number} merged",
#                 blocks=_format_pr_merged_blocks(event),
#             )
#             notification_text = "PR Merge Notification Sent"
#             await _broadcast_slack_card("Code Push Detected", event)

#         elif event.event_type == EventType.GITHUB_PR_CLOSED:
#             await slack.send_message(
#                 channel=settings.default_slack_channel,
#                 text=f"PR #{event.pr_number} closed",
#             )
#             notification_text = "PR Close Notification Sent"
#             await _broadcast_slack_card("Code Push Detected", event)

#         elif event.event_type == EventType.JIRA_ISSUE_CREATED:
#             await slack.send_message(
#                 channel=settings.default_slack_channel,
#                 text=f"Jira issue created: {event.jira_issue_key}",
#             )
#             notification_text = "Jira Creation Notification Sent"
#             await _broadcast_slack_card("Code Push Detected", event)

#         elif event.event_type == EventType.JIRA_ISSUE_UPDATED:
#             await slack.send_message(
#                 channel=settings.default_slack_channel,
#                 text=f"Jira issue updated: {event.jira_issue_key}",
#             )
#             notification_text = "Jira Update Notification Sent"
#             await _broadcast_slack_card("Code Push Detected", event)

#         else:
#             await slack.send_message(
#                 channel=settings.default_slack_channel,
#                 text=f"Event received: {event.event_type}",
#             )

#         # --- YAHAN BROADCAST KAREIN ---
#         await ws_manager.broadcast({
#             "type": "slack_notification",
#             "event": event.event_type,
#             "message": notification_text
#         })

#         actions.append("slack_notification_sent")
#         logger.info(f"[Slack Notifier] Sent and Broadcasted: {event.event_type}")

#     except Exception as e:
#         msg = f"slack_notify_failed: {str(e)}"
#         errors.append(msg)
#         logger.error(f"[Slack Notifier] {msg}")

#     return {"actions_taken": actions, "errors": errors, "next_action": "finalize"}

# """
# =============================================================================
# backend/agent/nodes/slack_notifier_node.py — SLACK NOTIFIER NODE
# =============================================================================
# """

# import time
# from backend.agent.state import AgentState
# from backend.agent.tools.slack_tool import SlackTool
# from backend.core.config import settings
# from backend.core.logger import get_logger
# from backend.models.events import EventType, IncomingEvent
# from backend.main import ws_manager

# logger = get_logger(__name__)

# # --- BLOCK FORMATTERS ---

# def _format_push_blocks(event: IncomingEvent) -> list[dict]:
#     pusher = event.pusher or event.pr_author or "Unknown Developer"
#     commit_sha = (event.commit_sha or "")[:8] or "N/A"
#     branch = event.branch or "N/A"
#     repo = event.repo or "N/A"
#     commit_msg = event.commit_msg or "No commit message"
#     timestamp = int(event.received_at or time.time())
#     commit_url = f"https://github.com/{repo}/commit/{event.commit_sha}" if event.repo and event.commit_sha else "#"
#     repo_url = f"https://github.com/{repo}" if repo != "N/A" else "#"

#     return [
#         {"type": "header", "text": {"type": "plain_text", "text": "Code Push Detected", "emoji": False}},
#         {"type": "section", "fields": [{"type": "mrkdwn", "text": f"*Developer*\n`{pusher}`"}, {"type": "mrkdwn", "text": f"*Time*\n<!date^{timestamp}^{{date_short_pretty}} at {{time}}|just now>"}]},
#         {"type": "divider"},
#         {"type": "section", "fields": [{"type": "mrkdwn", "text": f"*Repository*\n<{repo_url}|`{repo}`>"}, {"type": "mrkdwn", "text": f"*Branch*\n`{branch}`"}]},
#         {"type": "section", "fields": [{"type": "mrkdwn", "text": f"*Commit*\n<{commit_url}|`{commit_sha}`>"}, {"type": "mrkdwn", "text": f"*Message*\n{commit_msg[:80]}"}]},
#         {"type": "divider"},
#         {"type": "context", "elements": [{"type": "mrkdwn", "text": f"DevOps Orchestrator | Push Monitor | `{repo}`"}]}
#     ]

# def _format_pr_merged_blocks(event: IncomingEvent) -> list[dict]:
#     pr_url = f"https://github.com/{event.repo}/pull/{event.pr_number}" if event.repo and event.pr_number else "#"
#     timestamp = int(event.received_at or time.time())
#     return [
#         {"type": "header", "text": {"type": "plain_text", "text": f"Pull Request Merged — PR #{event.pr_number or 'N/A'}", "emoji": False}},
#         {"type": "section", "text": {"type": "mrkdwn", "text": f"*<{pr_url}|{event.pr_title or 'Untitled PR'}>*"}},
#         {"type": "section", "fields": [{"type": "mrkdwn", "text": f"*Merged By*\n`{event.pr_author or 'Unknown'}`"}, {"type": "mrkdwn", "text": f"*Time*\n<!date^{timestamp}^{{date_short_pretty}} at {{time}}|just now>"}, {"type": "mrkdwn", "text": f"*Repository*\n`{event.repo or 'N/A'}`"}, {"type": "mrkdwn", "text": f"*Target Branch*\n`{event.branch or 'main'}`"}]},
#         {"type": "divider"},
#         {"type": "context", "elements": [{"type": "mrkdwn", "text": f"DevOps Orchestrator | `{event.repo or 'N/A'}`"}]}
#     ]

# # --- DYNAMIC BROADCAST HELPER ---

# async def _broadcast_slack_card(title: str, event: IncomingEvent, blocks: list[dict]):
#     """Dynamic helper jo title aur sahi blocks dono accept karta hai."""
#     await ws_manager.broadcast({
#         "type": "slack_card",
#         "title": title,
#         "details": {
#             "pusher": event.pusher or event.pr_author or "N/A",
#             "branch": event.branch or "N/A",
#             "repo": event.repo or "N/A",
#             "message": event.commit_msg or event.pr_title or "No details"
#         },
#         "blocks": blocks
#     })

# # --- MAIN NODE ---

# async def notify_slack_node(state: AgentState) -> dict:
#     event = state["event"]
#     actions = list(state.get("actions_taken", []))
#     errors = list(state.get("errors", []))
#     slack = SlackTool()

#     try:
#         # Define logic based on event type
#         if event.event_type == EventType.GITHUB_PUSH:
#             blocks = _format_push_blocks(event)
#             await slack.send_message(channel=settings.default_slack_channel, text="Code push detected", blocks=blocks)
#             await _broadcast_slack_card("Code Push Detected", event, blocks)
#             notification_text = "Code Push Notification Sent"

#         elif event.event_type == EventType.GITHUB_PR_MERGED:
#             blocks = _format_pr_merged_blocks(event)
#             await slack.send_message(channel=settings.default_slack_channel, text="PR Merged", blocks=blocks)
#             await _broadcast_slack_card("PR Merged", event, blocks)
#             notification_text = "PR Merge Notification Sent"

#         else:
#             # Fallback for others
#             await slack.send_message(channel=settings.default_slack_channel, text=f"Event: {event.event_type}")
#             notification_text = "Standard Notification Sent"

#         actions.append("slack_notification_sent")
#         logger.info(f"[Slack Notifier] Success: {event.event_type}")

#     except Exception as e:
#         msg = f"slack_notify_failed: {str(e)}"
#         errors.append(msg)
#         logger.error(f"[Slack Notifier] {msg}")

#     return {"actions_taken": actions, "errors": errors, "next_action": "finalize"}

 
"""
=============================================================================
backend/agent/nodes/slack_notifier_node.py — SLACK NOTIFIER NODE
=============================================================================
"""
 
import time
from backend.agent.state import AgentState
from backend.agent.tools.slack_tool import SlackTool
from backend.core.config import settings
from backend.core.logger import get_logger
from backend.models.events import EventType, IncomingEvent
from backend.core.websocket import ws_manager
 
logger = get_logger(__name__)
 
# --- BLOCK FORMATTERS ---
 
def _format_push_blocks(event: IncomingEvent, summary: str) -> list[dict]:
    pusher = event.pusher or event.pr_author or "Unknown Developer"
    commit_sha = (event.commit_sha or "")[:8] or "N/A"
    branch = event.branch or "N/A"
    repo = event.repo or "N/A"
    commit_msg = event.commit_msg or "No commit message"
    timestamp = int(event.received_at or time.time())
    commit_url = f"https://github.com/{repo}/commit/{event.commit_sha}" if event.repo and event.commit_sha else "#"
    repo_url = f"https://github.com/{repo}" if repo != "N/A" else "#"
 
    return [
        {"type": "header", "text": {"type": "plain_text", "text": "Code Push Detected", "emoji": False}},
        {"type": "section", "fields": [{"type": "mrkdwn", "text": f"*Developer*\n`{pusher}`"}, {"type": "mrkdwn", "text": f"*Time*\n<!date^{timestamp}^{{date_short_pretty}} at {{time}}|just now>"}]},
        {"type": "divider"},
        {"type": "section", "fields": [{"type": "mrkdwn", "text": f"*Repository*\n<{repo_url}|`{repo}`>"}, {"type": "mrkdwn", "text": f"*Branch*\n`{branch}`"}]},
        {"type": "section", "fields": [{"type": "mrkdwn", "text": f"*Commit*\n<{commit_url}|`{commit_sha}`>"}, {"type": "mrkdwn", "text": f"*Message*\n{commit_msg[:80]}"}]},
        # AI Simplified Summary Add Kiya Gaya Hai
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*AI Simplified Summary:*\n_{summary}_"}},
        {"type": "divider"},
        {"type": "context", "elements": [{"type": "mrkdwn", "text": f"DevOps Orchestrator | Push Monitor | `{repo}`"}]}
    ]
 
def _format_pr_merged_blocks(event: IncomingEvent, summary: str) -> list[dict]:
    pr_url = f"https://github.com/{event.repo}/pull/{event.pr_number}" if event.repo and event.pr_number else "#"
    timestamp = int(event.received_at or time.time())
    return [
        {"type": "header", "text": {"type": "plain_text", "text": f"Pull Request Merged — PR #{event.pr_number or 'N/A'}", "emoji": False}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*<{pr_url}|{event.pr_title or 'Untitled PR'}>*"}},
        {"type": "section", "fields": [{"type": "mrkdwn", "text": f"*Merged By*\n`{event.pr_author or 'Unknown'}`"}, {"type": "mrkdwn", "text": f"*Time*\n<!date^{timestamp}^{{date_short_pretty}} at {{time}}|just now>"}, {"type": "mrkdwn", "text": f"*Repository*\n`{event.repo or 'N/A'}`"}, {"type": "mrkdwn", "text": f"*Target Branch*\n`{event.branch or 'main'}`"}]},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*AI Simplified Summary:*\n_{summary}_"}},
        {"type": "divider"},
        {"type": "context", "elements": [{"type": "mrkdwn", "text": f"DevOps Orchestrator | `{event.repo or 'N/A'}`"}]}
    ]
 
# --- DYNAMIC BROADCAST HELPER ---
 
async def _broadcast_slack_card(title: str, event: IncomingEvent, blocks: list[dict], summary: str):
    """Frontend ko update karne ke liye summary payload mein add ki."""
    try:
        await ws_manager.broadcast({
        "type": "slack_card",
        "title": title,
        "details": {
            "pusher": event.pusher or event.pr_author or "N/A",
            "branch": event.branch or "N/A",
            "repo": event.repo or "N/A",
            "message": event.commit_msg or event.pr_title or "No details",
            "summary": summary
        },
        "blocks": blocks
        })
        logger.info(f"[Slack Notifier] Slack card broadcasted successfully: {title}")
    except Exception as e:
        logger.error(f"[Slack Notifier] WebSocket broadcast failed: {e}")
 
# --- MAIN NODE ---
 
async def notify_slack_node(state: AgentState) -> dict:
    event = state["event"]
    summary = state.get("analysis_summary") or "No changes detected or summary not available."
    actions = list(state.get("actions_taken", []))
    errors = list(state.get("errors", []))
    slack = SlackTool()
 
    logger.info(f"[Slack Notifier] Processing event: {event.event_type}")
 
    try:
        if event.event_type == EventType.GITHUB_PUSH:
            blocks = _format_push_blocks(event, summary) # Summary pass ki
            await slack.send_message(channel=settings.default_slack_channel, text="Code push detected", blocks=blocks)
            await _broadcast_slack_card("Code Push Detected", event, blocks, summary)
            actions.append("slack_push_notification_sent")
            # notification_text = " Push Notification Sent"
 
        elif event.event_type == EventType.GITHUB_PR_MERGED:
            blocks = _format_pr_merged_blocks(event, summary)
            await slack.send_message(channel=settings.default_slack_channel, text="PR Merged", blocks=blocks)
            await _broadcast_slack_card("PR Merged", event, blocks, summary)
            actions.append("slack_merge_notification_sent")
            # notification_text = "PR Merge Notification Sent"
 
        else:
            await slack.send_message(channel=settings.default_slack_channel, text=f"Event: {event.event_type}")
            actions.append("slack_standard_notification_sent")
            # notification_text = "Standard Notification Sent"
 
        # actions.append("slack_notification_sent")
        logger.info(f"[Slack Notifier] Success: {event.event_type}")
 
    except Exception as e:
        msg = f"slack_notify_failed: {str(e)}"
        errors.append(msg)
        logger.error(f"[Slack Notifier] {msg}")
 
    return {"actions_taken": actions, "errors": errors, "next_action": "finalize"}