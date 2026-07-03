# """
# =============================================================================
# backend/agent/tools/slack_tool.py — SLACK MCP TOOL
# =============================================================================
# Slack Web API wrapper — professional messages.

# METHODS:
#   send_message()           — Plain ya Block Kit message
#   send_pr_alert()          — PR review professional card
#   send_jira_created_card() — Jira ticket creation card
#   send_error_alert()       — System error alert
#   send_daily_report()      — End of day report
# =============================================================================
# """

# import time
# from typing import TYPE_CHECKING, Any

# import httpx

# from backend.core.config import settings
# from backend.core.logger import get_logger
# from backend.models.responses import PRAnalysisResult

# if TYPE_CHECKING:
#     from backend.models.events import IncomingEvent

# logger = get_logger(__name__)

# RISK_DECISION = {
#     "low":      "Approved for Merge",
#     "medium":   "Review Recommended",
#     "high":     "Review Required",
#     "critical": "DO NOT MERGE",
# }

# RISK_LABEL = {
#     "low":      "LOW",
#     "medium":   "MEDIUM",
#     "high":     "HIGH",
#     "critical": "CRITICAL",
# }


# class SlackTool:
#     """Slack Web API wrapper."""

#     def __init__(self):
#         self.base_url = settings.slack_api_url
#         self.headers  = {
#             "Authorization": f"Bearer {settings.slack_bot_token}",
#             "Content-Type":  "application/json",
#         }

#     # ==========================================================================
#     # CORE SEND
#     # ==========================================================================

#     async def send_message(
#         self,
#         channel: str,
#         text:    str,
#         blocks:  list[dict] | None = None,
#     ) -> dict:
#         """Slack channel mein message bhejo."""
#         payload: dict[str, Any] = {"channel": channel, "text": text}
#         if blocks:
#             payload["blocks"] = blocks

#         async with httpx.AsyncClient(timeout=30.0) as client:
#             resp = await client.post(
#                 f"{self.base_url}/chat.postMessage",
#                 headers=self.headers,
#                 json=payload,
#             )
#             resp.raise_for_status()
#             data = resp.json()

#         if not data.get("ok"):
#             raise RuntimeError(f"Slack API error: {data.get('error')}")

#         logger.info(f"[Slack] Message sent to {channel}")
#         return {"ts": data["ts"], "channel": data["channel"]}

#     # ==========================================================================
#     # PR REVIEW CARD
#     # ==========================================================================

#     def _build_pr_blocks(self, event: "IncomingEvent", analysis: PRAnalysisResult) -> list[dict]:
#         """Professional PR review card."""
#         risk        = analysis.risk_level
#         decision    = RISK_DECISION.get(risk, "Review")
#         risk_label  = RISK_LABEL.get(risk, risk.upper())

#         status_map = {
#             "low":      "Approved — No action required",
#             "medium":   "Under Review — Team attention needed",
#             "high":     "Blocked — Mandatory review required",
#             "critical": "Blocked — Security review required",
#         }
#         status_line = status_map.get(risk, "Review pending")

#         concerns_text = (
#             "\n".join(f"  • {c}" for c in analysis.concerns)
#             if analysis.concerns else "  None identified"
#         )
#         positives_text = (
#             "\n".join(f"  • {p}" for p in getattr(analysis, "positive_aspects", []))
#             if getattr(analysis, "positive_aspects", []) else "  N/A"
#         )
#         reviewers_text = (
#             ", ".join(getattr(analysis, "suggested_reviewers", []))
#             if getattr(analysis, "suggested_reviewers", []) else "No specific expertise required"
#         )

#         review_time  = getattr(analysis, "estimated_review_time", "N/A")
#         pr_url       = f"https://github.com/{event.repo}/pull/{event.pr_number}"
#         merge_status = (
#             "Auto-merged successfully"
#             if analysis.auto_merge and risk == "low"
#             else "Awaiting review"
#         )
#         ts = int(time.time())

#         return [
#             {
#                 "type": "header",
#                 "text": {"type": "plain_text", "text": f"Code Review Report — PR #{event.pr_number}", "emoji": False},
#             },
#             {
#                 "type": "section",
#                 "text": {"type": "mrkdwn", "text": f"*Status:* {status_line}"},
#             },
#             {"type": "divider"},
#             {
#                 "type": "section",
#                 "text": {
#                     "type": "mrkdwn",
#                     "text": (
#                         f"*<{pr_url}|{event.pr_title}>*\n"
#                         f"Repository: `{event.repo}`\n"
#                         f"Author: `{event.pr_author}`   |   Branch: `{event.branch or 'N/A'}`"
#                     ),
#                 },
#             },
#             {"type": "divider"},
#             {
#                 "type": "section",
#                 "fields": [
#                     {"type": "mrkdwn", "text": f"*Risk Level*\n`{risk_label}`"},
#                     {"type": "mrkdwn", "text": f"*Decision*\n{decision}"},
#                     {"type": "mrkdwn", "text": f"*Merge Status*\n{merge_status}"},
#                     {"type": "mrkdwn", "text": f"*Est. Review Time*\n{review_time}"},
#                 ],
#             },
#             {"type": "divider"},
#             {
#                 "type": "section",
#                 "text": {"type": "mrkdwn", "text": f"*Summary*\n{analysis.summary}"},
#             },
#             {
#                 "type": "section",
#                 "text": {"type": "mrkdwn", "text": f"*Issues Found*\n{concerns_text}"},
#             },
#             {
#                 "type": "section",
#                 "text": {"type": "mrkdwn", "text": f"*Strengths*\n{positives_text}"},
#             },
#             {
#                 "type": "section",
#                 "text": {"type": "mrkdwn", "text": f"*Recommended Reviewer Expertise*\n{reviewers_text}"},
#             },
#             {"type": "divider"},
#             {
#                 "type": "context",
#                 "elements": [
#                     {
#                         "type": "mrkdwn",
#                         "text": (
#                             f"DevOps Orchestrator  |  Automated Code Review  |  "
#                             f"`{event.repo}`  |  "
#                             f"<!date^{ts}^{{date_short_pretty}} {{time}}|just now>"
#                         ),
#                     }
#                 ],
#             },
#         ]

#     async def send_pr_alert(self, event: "IncomingEvent", analysis: PRAnalysisResult) -> dict:
#         """PR review card Slack pe bhejo."""
#         blocks = self._build_pr_blocks(event, analysis)
#         risk   = analysis.risk_level
#         text   = f"Code Review Report — PR #{event.pr_number}: {event.pr_title} | Risk: {RISK_LABEL.get(risk, risk.upper())}"
#         return await self.send_message(channel=settings.default_slack_channel, text=text, blocks=blocks)

#     # ==========================================================================
#     # JIRA TICKET CARD
#     # ==========================================================================

#     async def send_jira_created_card(
#         self,
#         channel:     str,
#         issue_key:   str,
#         issue_url:   str,
#         summary:     str,
#         issue_type:  str,
#         priority:    str,
#         description: str,
#         labels:      list[str],
#         reporter:    str,
#     ) -> dict:
#         """Jira ticket creation ka professional card."""
#         labels_text  = "  " + "   ".join(f"`{l}`" for l in labels) if labels else "  None"
#         desc_preview = description[:200] + "..." if len(description) > 200 else description

#         blocks = [
#             {
#                 "type": "header",
#                 "text": {"type": "plain_text", "text": f"New {issue_type} Logged — {issue_key}", "emoji": False},
#             },
#             {
#                 "type": "section",
#                 "text": {"type": "mrkdwn", "text": f"*<{issue_url}|{summary}>*"},
#             },
#             {"type": "divider"},
#             {
#                 "type": "section",
#                 "fields": [
#                     {"type": "mrkdwn", "text": f"*Issue ID*\n`{issue_key}`"},
#                     {"type": "mrkdwn", "text": f"*Type*\n{issue_type}"},
#                     {"type": "mrkdwn", "text": f"*Priority*\n{priority}"},
#                     {"type": "mrkdwn", "text": f"*Reported By*\n{reporter}"},
#                 ],
#             },
#             {
#                 "type": "section",
#                 "text": {"type": "mrkdwn", "text": f"*Labels*\n{labels_text}"},
#             },
#             {
#                 "type": "section",
#                 "text": {"type": "mrkdwn", "text": f"*Description*\n>{desc_preview}"},
#             },
#             {"type": "divider"},
#             {
#                 "type": "section",
#                 "text": {"type": "mrkdwn", "text": f"*<{issue_url}|View in Jira>*"},
#             },
#             {
#                 "type": "context",
#                 "elements": [
#                     {
#                         "type": "mrkdwn",
#                         "text": f"DevOps Orchestrator  |  Issue Tracker  |  Project: `{settings.jira_project_key}`",
#                     }
#                 ],
#             },
#         ]

#         return await self.send_message(
#             channel=channel,
#             text=f"New {issue_type} logged: {issue_key} — {summary}",
#             blocks=blocks,
#         )

#     # ==========================================================================
#     # ERROR ALERT
#     # ==========================================================================

#     async def send_error_alert(
#         self,
#         channel:    str,
#         error_type: str,
#         short_msg:  str,
#         detail:     str,
#         source:     str = "System",
#     ) -> dict:
#         """System error ka professional alert."""
#         ts = int(time.time())
#         blocks = [
#             {
#                 "type": "header",
#                 "text": {"type": "plain_text", "text": f"System Alert — {error_type}", "emoji": False},
#             },
#             {
#                 "type": "section",
#                 "fields": [
#                     {"type": "mrkdwn", "text": f"*Error*\n`{short_msg}`"},
#                     {"type": "mrkdwn", "text": f"*Source*\n`{source}`"},
#                 ],
#             },
#             {
#                 "type": "section",
#                 "text": {"type": "mrkdwn", "text": f"*Details*\n>{detail[:300]}"},
#             },
#             {"type": "divider"},
#             {
#                 "type": "context",
#                 "elements": [
#                     {
#                         "type": "mrkdwn",
#                         "text": f"DevOps Orchestrator  |  <!date^{ts}^{{date_short_pretty}} {{time}}|just now>",
#                     }
#                 ],
#             },
#         ]

#         return await self.send_message(
#             channel=channel,
#             text=f"System Alert: {short_msg} ({source})",
#             blocks=blocks,
#         )

#     # ==========================================================================
#     # END OF DAY REPORT
#     # ==========================================================================

#     async def send_daily_report(
#         self,
#         channel:      str,
#         date:         str,
#         total_prs:    int,
#         merged_prs:   int,
#         blocked_prs:  int,
#         total_pushes: int,
#         risk_summary: dict,
#         issues_found: list[str],
#         jira_created: int,
#         contributors: list[str],
#         highlights:   list[str],
#     ) -> dict:
#         """End of Day professional report — team ki daily progress."""
#         issues_text = (
#             "\n".join(f"  • {i}" for i in issues_found[:5])
#             if issues_found else "  No issues detected"
#         )
#         highlights_text = (
#             "\n".join(f"  • {h}" for h in highlights[:5])
#             if highlights else "  No highlights"
#         )
#         contributors_text = (
#             ", ".join(f"`{c}`" for c in contributors)
#             if contributors else "No activity"
#         )
#         risk_text = (
#             f"  Low: {risk_summary.get('low', 0)}   "
#             f"Medium: {risk_summary.get('medium', 0)}   "
#             f"High: {risk_summary.get('high', 0)}   "
#             f"Critical: {risk_summary.get('critical', 0)}"
#         )

#         blocks = [
#             {
#                 "type": "header",
#                 "text": {"type": "plain_text", "text": f"Daily Development Report — {date}", "emoji": False},
#             },
#             {
#                 "type": "section",
#                 "text": {
#                     "type": "mrkdwn",
#                     "text": (
#                         f"Summary of all development activity recorded today.\n"
#                         f"*Active Contributors:* {contributors_text}"
#                     ),
#                 },
#             },
#             {"type": "divider"},
#             {
#                 "type": "section",
#                 "text": {"type": "mrkdwn", "text": "*Activity Summary*"},
#             },
#             {
#                 "type": "section",
#                 "fields": [
#                     {"type": "mrkdwn", "text": f"*Pull Requests*\n{total_prs} opened"},
#                     {"type": "mrkdwn", "text": f"*Merged*\n{merged_prs} merged"},
#                     {"type": "mrkdwn", "text": f"*Blocked*\n{blocked_prs} blocked"},
#                     {"type": "mrkdwn", "text": f"*Code Pushes*\n{total_pushes} pushes"},
#                     {"type": "mrkdwn", "text": f"*Jira Tickets*\n{jira_created} created"},
#                 ],
#             },
#             {"type": "divider"},
#             {
#                 "type": "section",
#                 "text": {"type": "mrkdwn", "text": f"*Risk Breakdown*\n{risk_text}"},
#             },
#             {"type": "divider"},
#             {
#                 "type": "section",
#                 "text": {"type": "mrkdwn", "text": f"*Highlights*\n{highlights_text}"},
#             },
#             {
#                 "type": "section",
#                 "text": {"type": "mrkdwn", "text": f"*Issues Detected*\n{issues_text}"},
#             },
#             {"type": "divider"},
#             {
#                 "type": "context",
#                 "elements": [
#                     {
#                         "type": "mrkdwn",
#                         "text": f"DevOps Orchestrator  |  Automated Daily Report  |  {date}",
#                     }
#                 ],
#             },
#         ]

#         return await self.send_message(
#             channel=channel,
#             text=f"Daily Development Report — {date}",
#             blocks=blocks,
#         )

"""
=============================================================================
app/agent/tools/slack_tool.py — SLACK MCP TOOL (Professional Version)
=============================================================================
PURPOSE:
  Professional Slack messages — human-written feel, no AI artifacts.
  End of Day report — team ki daily progress ek jagah.
=============================================================================
"""

import time
from typing import TYPE_CHECKING, Any

import httpx

from backend.core.config import settings
from backend.core.logger import get_logger
from backend.models.responses import PRAnalysisResult

if TYPE_CHECKING:
    from backend.models.events import IncomingEvent

logger = get_logger(__name__)

RISK_DECISION = {
    "low":      "Approved for Merge",
    "medium":   "Review Recommended",
    "high":     "Review Required",
    "critical": "DO NOT MERGE",
}

RISK_LABEL = {
    "low":      "LOW",
    "medium":   "MEDIUM",
    "high":     "HIGH",
    "critical": "CRITICAL",
}

PRIORITY_COLOR = {
    "low":      "#2ECC71",   # Green
    "medium":   "#F39C12",   # Orange
    "high":     "#E74C3C",   # Red
    "critical": "#8E44AD",   # Purple
}


class SlackTool:
    """Slack Web API wrapper — professional messages."""

    def __init__(self):
        self.base_url = settings.slack_api_url
        self.headers  = {
            "Authorization": f"Bearer {settings.slack_bot_token}",
            "Content-Type":  "application/json",
        }

    async def send_message(
        self,
        channel: str,
        text:    str,
        blocks:  list[dict] | None = None,
    ) -> dict:
        """Core send method."""
        payload: dict[str, Any] = {"channel": channel, "text": text}
        if blocks:
            payload["blocks"] = blocks

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat.postMessage",
                headers=self.headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        if not data.get("ok"):
            raise RuntimeError(f"Slack API error: {data.get('error')}")

        logger.info(f"[Slack] Message sent to {channel}")
        return {"ts": data["ts"], "channel": data["channel"]}

    # ==========================================================================
    # PR REVIEW CARD — Professional
    # ==========================================================================

    def _build_pr_blocks(
        self,
        event:    "IncomingEvent",
        analysis: PRAnalysisResult,
    ) -> list[dict]:
        """
        Professional PR review card.
        Clean, structured — looks like a human wrote it.
        """
        risk        = analysis.risk_level
        decision    = RISK_DECISION.get(risk, "Review")
        risk_label  = RISK_LABEL.get(risk, risk.upper())

        # Status line
        status_map = {
            "low":      "Approved — No action required",
            "medium":   "Under Review — Team attention needed",
            "high":     "Blocked — Mandatory review required",
            "critical": "Blocked — Security review required",
        }
        status_line = status_map.get(risk, "Review pending")

        # Concerns
        concerns_text = (
            "\n".join(f"  • {c}" for c in analysis.concerns)
            if analysis.concerns
            else "  None identified"
        )

        # Positives
        positives = getattr(analysis, "positive_aspects", [])
        positives_text = (
            "\n".join(f"  • {p}" for p in positives)
            if positives
            else "  N/A"
        )

        # Reviewers
        reviewers = getattr(analysis, "suggested_reviewers", [])
        reviewers_text = (
            ", ".join(reviewers) if reviewers
            else "No specific expertise required"
        )

        review_time = getattr(analysis, "estimated_review_time", "N/A")
        pr_url      = f"https://github.com/{event.repo}/pull/{event.pr_number}"

        # Merge status
        merge_status = (
            "Auto-merged successfully"
            if analysis.auto_merge and risk == "low"
            else "Awaiting review"
        )

        return [
            # ── HEADER ────────────────────────────────────────────────────────
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Code Review Report — PR #{event.pr_number}",
                    "emoji": False,
                },
            },

            # ── STATUS BAR ────────────────────────────────────────────────────
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Status:* {status_line}",
                },
            },

            {"type": "divider"},

            # ── PR DETAILS ────────────────────────────────────────────────────
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*<{pr_url}|{event.pr_title}>*\n"
                        f"Repository: `{event.repo}`\n"
                        f"Author: `{event.pr_author}`   |   "
                        f"Branch: `{event.branch or 'N/A'}`"
                    ),
                },
            },

            {"type": "divider"},

            # ── RISK ASSESSMENT ───────────────────────────────────────────────
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Risk Level*\n`{risk_label}`",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Decision*\n{decision}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Merge Status*\n{merge_status}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Est. Review Time*\n{review_time}",
                    },
                ],
            },

            {"type": "divider"},

            # ── SUMMARY ───────────────────────────────────────────────────────
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary*\n{analysis.summary}",
                },
            },

            # ── CONCERNS ─────────────────────────────────────────────────────
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Issues Found*\n{concerns_text}",
                },
            },

            # ── POSITIVES ────────────────────────────────────────────────────
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Strengths*\n{positives_text}",
                },
            },

            # ── REVIEWERS ────────────────────────────────────────────────────
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Recommended Reviewer Expertise*\n{reviewers_text}",
                },
            },

            {"type": "divider"},

            # ── FOOTER ───────────────────────────────────────────────────────
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"DevOps Orchestrator  |  "
                            f"Automated Code Review  |  "
                            f"`{event.repo}`  |  "
                            f"<!date^{int(time.time())}^{{date_short_pretty}} {{time}}|just now>"
                        ),
                    }
                ],
            },
        ]

    async def send_pr_alert(
        self,
        event:    "IncomingEvent",
        analysis: PRAnalysisResult,
    ) -> dict:
        """PR review ka professional card bhejo."""
        blocks = self._build_pr_blocks(event, analysis)
        risk   = analysis.risk_level
        text   = (
            f"Code Review Report — PR #{event.pr_number}: "
            f"{event.pr_title} | Risk: {RISK_LABEL.get(risk, risk.upper())}"
        )
        return await self.send_message(
            channel=settings.default_slack_channel,
            text=text,
            blocks=blocks,
        )

    # ==========================================================================
    # JIRA TICKET CARD — Professional
    # ==========================================================================

    async def send_jira_created_card(
        self,
        channel:     str,
        issue_key:   str,
        issue_url:   str,
        summary:     str,
        issue_type:  str,
        priority:    str,
        description: str,
        labels:      list[str],
        reporter:    str,
    ) -> dict:
        """Jira ticket creation ka professional card."""

        labels_text = (
            "  " + "   ".join(f"`{l}`" for l in labels)
            if labels else "  None"
        )

        desc_preview = (
            description[:200] + "..."
            if len(description) > 200
            else description
        )

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"New {issue_type} Logged — {issue_key}",
                    "emoji": False,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{issue_url}|{summary}>*",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Issue ID*\n`{issue_key}`"},
                    {"type": "mrkdwn", "text": f"*Type*\n{issue_type}"},
                    {"type": "mrkdwn", "text": f"*Priority*\n{priority}"},
                    {"type": "mrkdwn", "text": f"*Reported By*\n{reporter}"},
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Labels*\n{labels_text}"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description*\n>{desc_preview}",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{issue_url}|View in Jira>*",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"DevOps Orchestrator  |  "
                            f"Issue Tracker  |  "
                            f"Project: `{settings.jira_project_key}`"
                        ),
                    }
                ],
            },
        ]

        return await self.send_message(
            channel=channel,
            text=f"New {issue_type} logged: {issue_key} — {summary}",
            blocks=blocks,
        )

    # ==========================================================================
    # ERROR ALERT — Professional
    # ==========================================================================

    async def send_error_alert(
        self,
        channel:    str,
        error_type: str,
        short_msg:  str,
        detail:     str,
        source:     str = "System",
    ) -> dict:
        """System error ka professional alert."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"System Alert — {error_type}",
                    "emoji": False,
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Error*\n`{short_msg}`"},
                    {"type": "mrkdwn", "text": f"*Source*\n`{source}`"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Details*\n>{detail[:300]}",
                },
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"DevOps Orchestrator  |  "
                            f"<!date^{int(time.time())}^{{date_short_pretty}} {{time}}|just now>"
                        ),
                    }
                ],
            },
        ]

        return await self.send_message(
            channel=channel,
            text=f"System Alert: {short_msg} ({source})",
            blocks=blocks,
        )

    # ==========================================================================
    # END OF DAY REPORT — Professional Daily Summary
    # ==========================================================================

    async def send_daily_report(
        self,
        channel:      str,
        date:         str,
        total_prs:    int,
        merged_prs:   int,
        blocked_prs:  int,
        total_pushes: int,
        risk_summary: dict,      # {"low": 3, "medium": 1, "high": 1, "critical": 0}
        issues_found: list[str], # ["No rate limiting on PR #3", ...]
        jira_created: int,
        contributors: list[str], # ["Muinam", "john_doe"]
        highlights:   list[str], # ["PR #1 auto-merged", "Critical issue blocked"]
    ) -> dict:
        """
        End of Day professional report.
        Team ko ek jagah poori din ki progress dikhti hai.
        """
        # Agar koi data nahi toh N/A
        issues_text = (
            "\n".join(f"  • {i}" for i in issues_found[:5])
            if issues_found else "  No issues detected"
        )

        highlights_text = (
            "\n".join(f"  • {h}" for h in highlights[:5])
            if highlights else "  No highlights"
        )

        contributors_text = (
            ", ".join(f"`{c}`" for c in contributors)
            if contributors else "No activity"
        )

        # Risk breakdown
        risk_text = (
            f"  Low: {risk_summary.get('low', 0)}   "
            f"Medium: {risk_summary.get('medium', 0)}   "
            f"High: {risk_summary.get('high', 0)}   "
            f"Critical: {risk_summary.get('critical', 0)}"
        )

        blocks = [
            # ── HEADER ────────────────────────────────────────────────────────
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Daily Development Report — {date}",
                    "emoji": False,
                },
            },

            # ── INTRO ─────────────────────────────────────────────────────────
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"Here is a summary of all development activity "
                        f"recorded today across the repository.\n"
                        f"*Active Contributors:* {contributors_text}"
                    ),
                },
            },

            {"type": "divider"},

            # ── KEY METRICS ───────────────────────────────────────────────────
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Activity Summary*",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Pull Requests*\n{total_prs} opened",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Merged*\n{merged_prs} merged",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Blocked*\n{blocked_prs} blocked",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Code Pushes*\n{total_pushes} pushes",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Jira Tickets*\n{jira_created} created",
                    },
                ],
            },

            {"type": "divider"},

            # ── RISK BREAKDOWN ────────────────────────────────────────────────
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Risk Breakdown*\n{risk_text}",
                },
            },

            {"type": "divider"},

            # ── HIGHLIGHTS ────────────────────────────────────────────────────
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Highlights*\n{highlights_text}",
                },
            },

            # ── ISSUES ───────────────────────────────────────────────────────
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Issues Detected*\n{issues_text}",
                },
            },

            {"type": "divider"},

            # ── FOOTER ───────────────────────────────────────────────────────
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"DevOps Orchestrator  |  "
                            f"Automated Daily Report  |  "
                            f"{date}"
                        ),
                    }
                ],
            },
        ]

        return await self.send_message(
            channel=channel,
            text=f"Daily Development Report — {date}",
            blocks=blocks,
        )