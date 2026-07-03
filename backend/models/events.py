"""
=============================================================================
backend/models/events.py — EVENT DATA MODELS
=============================================================================
IncomingEvent = Universal format
GitHub + Slack + Jira ka alag format → ek IncomingEvent → AI Agent

EventType = Tamam supported events ki list
=============================================================================
"""

import time
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    GITHUB_PR_OPENED   = "github.pr.opened"
    GITHUB_PR_MERGED   = "github.pr.merged"
    GITHUB_PR_CLOSED   = "github.pr.closed"
    GITHUB_PUSH        = "github.push"
    SLACK_MESSAGE      = "slack.message"
    SLACK_COMMAND      = "slack.command"
    JIRA_ISSUE_CREATED = "jira.issue.created"
    JIRA_ISSUE_UPDATED = "jira.issue.updated"


class IncomingEvent(BaseModel):
    """
    Universal event — platform se independent.
    AI agent sirf ye dekhta hai.
    """
    # Required
    event_type: EventType
    source:     str

    # GitHub fields
    repo:       str | None = None
    pr_number:  int | None = None
    pr_title:   str | None = None
    pr_body:    str | None = None
    pr_author:  str | None = None
    branch:     str | None = None
    commit_sha: str | None = None
    pusher:     str | None = None  # Push karne wale developer ka naam
    commit_msg: str | None = None  # Last commit message

    # Slack fields
    slack_channel: str | None = None
    slack_user:    str | None = None
    slack_text:    str | None = None

    # Jira fields
    jira_issue_key: str | None = None
    jira_summary:   str | None = None
    jira_status:    str | None = None

    # Meta
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    received_at: float          = Field(default_factory=time.time)
