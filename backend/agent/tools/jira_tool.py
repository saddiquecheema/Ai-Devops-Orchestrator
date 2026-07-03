"""
=============================================================================
backend/agent/tools/jira_tool.py — JIRA MCP TOOL
=============================================================================
Jira REST API v3 wrapper.
AI Agent Jira mein issues banata aur update karta hai.

AUTH: Email + API Token (password nahi)
ADF:  Jira plain text nahi leta — Atlassian Document Format use hota hai
=============================================================================
"""

import httpx
from backend.core.config import settings
from backend.core.logger import get_logger
from backend.models.responses import JiraIssuePayload

logger = get_logger(__name__)


def _to_adf(text: str) -> dict:
    """Plain text → Atlassian Document Format (Jira ka required format)."""
    return {
        "type":    "doc",
        "version": 1,
        "content": [
            {
                "type":    "paragraph",
                "content": [{"type": "text", "text": text}],
            }
        ],
    }


class JiraTool:
    """Jira REST API v3 wrapper."""

    def __init__(self):
        self.base_url = f"{settings.jira_base_url}/rest/api/3"
        self.auth     = (settings.jira_email, settings.jira_api_token)
        self.headers  = {
            "Accept":       "application/json",
            "Content-Type": "application/json",
        }

    async def create_issue(self, payload: JiraIssuePayload) -> dict:
        """
        Naya Jira issue create karo.
        Returns: {key, id, url}
        """
        clean_labels = [label.replace(" ", "_") for label in payload.labels]

        body: dict = {
            "fields": {
                "project":     {"key": settings.jira_project_key},
                "summary":     payload.summary,
                "description": _to_adf(payload.description),
                "issuetype":   {"name": payload.issue_type},
                "priority":    {"name": payload.priority},
                "labels":      clean_labels,
            }
        }

        if payload.assignee_account_id:
            body["fields"]["assignee"] = {"accountId": payload.assignee_account_id}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/issue",
                auth=self.auth, headers=self.headers, json=body,
            )
            if resp.status_code >= 400:
                error_data = resp.json()
                logger.error(f"[Jira API Debug] Response: {error_data}") # Error details print karega
                resp.raise_for_status()

        data = resp.json()
        url  = f"{settings.jira_base_url}/browse/{data['key']}"
        logger.info(f"[Jira] Created {data['key']}: {payload.summary}")
        return {"key": data["key"], "id": data["id"], "url": url}

    async def update_issue_status(self, issue_key: str, transition_name: str) -> dict:
        """
        Issue ka status update karo — workflow transition.
        Step 1: Available transitions fetch karo
        Step 2: Matching transition ID dhoondho
        Step 3: Apply karo
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            t_resp = await client.get(
                f"{self.base_url}/issue/{issue_key}/transitions",
                auth=self.auth, headers=self.headers,
            )
            t_resp.raise_for_status()
            transitions = t_resp.json().get("transitions", [])

            target = next(
                (t for t in transitions if transition_name.lower() in t["name"].lower()),
                None,
            )
            if not target:
                available = [t["name"] for t in transitions]
                raise ValueError(f"Transition '{transition_name}' not found. Available: {available}")

            apply_resp = await client.post(
                f"{self.base_url}/issue/{issue_key}/transitions",
                auth=self.auth, headers=self.headers,
                json={"transition": {"id": target["id"]}},
            )
            apply_resp.raise_for_status()

        logger.info(f"[Jira] {issue_key} → {transition_name}")
        return {"issue_key": issue_key, "new_status": transition_name}

    async def add_comment(self, issue_key: str, text: str) -> dict:
        """Issue pe comment add karo."""
        body = {"body": _to_adf(text)}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/issue/{issue_key}/comment",
                auth=self.auth, headers=self.headers, json=body,
            )
            resp.raise_for_status()
        return {"comment_id": resp.json()["id"]}
