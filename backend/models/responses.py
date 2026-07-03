# """
# =============================================================================
# backend/models/responses.py — RESPONSE & RESULT MODELS
# =============================================================================
# PRAnalysisResult   — LLM ka PR review result
# JiraIssuePayload   — Jira ticket create karne ka data
# OrchestratorResponse — Final API response
# =============================================================================
# """

# from typing import Literal
# from pydantic import BaseModel, Field


# class PRAnalysisResult(BaseModel):
#     """
#     AI agent ka PR analysis result.
#     risk_level:
#       low      → docs/tests only         → auto-merge OK
#       medium   → new features with tests → human review suggested
#       high     → auth/DB changes         → human review required
#       critical → secrets/infra changes   → block + alert
#     """
#     is_safe_to_merge:      bool
#     risk_level:            Literal["low", "medium", "high", "critical"]
#     summary:               str
#     concerns:              list[str] = Field(default_factory=list)
#     positive_aspects:      list[str] = Field(default_factory=list)
#     suggested_reviewers:   list[str] = Field(default_factory=list)
#     auto_merge:            bool      = False
#     requires_tests:        bool      = False
#     estimated_review_time: str       = "N/A"


# class JiraIssuePayload(BaseModel):
#     """Jira issue create karne ka data. LLM Slack message se extract karta hai."""
#     summary:             str
#     description:         str
#     issue_type:          str       = "Task"
#     priority:            str       = "Medium"
#     labels:              list[str] = Field(default_factory=list)
#     assignee_account_id: str | None = None


# class OrchestratorResponse(BaseModel):
#     """Har webhook ke baad return hone wala response."""
#     success:            bool
#     event_type:         str
#     actions_taken:      list[str] = Field(default_factory=list)
#     errors:             list[str] = Field(default_factory=list)
#     processing_time_ms: float     = 0.0



"""
=============================================================================
app/models/responses.py — RESPONSE & RESULT DATA MODELS
=============================================================================
PURPOSE:
  Ye file define karti hai ke AI agent ke results aur API responses
  kaise dikhte hain.

MODELS:
  PRAnalysisResult   — LLM ka PR review result
  JiraIssuePayload   — Jira mein issue banane ka data
  SlackNotification  — Slack message ka format
  OrchestratorResponse — Final API response
=============================================================================
"""

from typing import Literal

from pydantic import BaseModel, Field


class PRAnalysisResult(BaseModel):
    """
    AI agent ka Pull Request review ka result.
    LLM se JSON mein ye exact format maanga jaata hai.

    risk_level ka matlab:
      low      → docs, tests, minor refactor — auto-merge safe
      medium   → new features with tests     — human review suggested
      high     → auth changes, DB changes    — human review required
      critical → secrets, breaking changes   — block merge, alert team
    """
    is_safe_to_merge:       bool
    risk_level:             Literal["low", "medium", "high", "critical"]
    summary:                str
    concerns:               list[str] = Field(default_factory=list)
    positive_aspects:       list[str] = Field(default_factory=list)   # Kya acha hai PR mein
    suggested_reviewers:    list[str] = Field(default_factory=list)
    auto_merge:             bool      = False
    requires_tests:         bool      = False   # Kya tests add karne chahiye?
    estimated_review_time:  str       = "N/A"   # "5 mins", "30 mins", "2 hours"


class JiraIssuePayload(BaseModel):
    """
    Jira mein issue create karne ke liye zaruri data.
    LLM Slack message se ye data extract karta hai.
    """
    summary:              str
    description:          str
    issue_type:           str       = "Task"   # Task | Bug | Story | Epic
    priority:             str       = "Medium" # Highest | High | Medium | Low | Lowest
    labels:               list[str] = Field(default_factory=list)
    assignee_account_id:  str | None = None    # Jira account ID (optional)


class SlackNotification(BaseModel):
    """
    Slack mein bhejne wala message.
    'blocks' = Slack Block Kit format — rich UI cards ke liye.
    """
    channel: str
    text:    str                                              # Fallback plain text
    blocks:  list[dict] = Field(default_factory=list)        # Optional rich format


class OrchestratorResponse(BaseModel):
    """
    Har webhook ke response mein ye return hota hai.
    Batata hai ke kya kya actions hue aur koi error tha ya nahi.

    Example:
      {
        "success": true,
        "event_type": "github.pr.opened",
        "actions_taken": ["pr_analyzed", "github_comment_posted", "slack_alert_sent"],
        "errors": [],
        "processing_time_ms": 1243.5
      }
    """
    success:             bool
    event_type:          str
    actions_taken:       list[str] = Field(default_factory=list)
    errors:              list[str] = Field(default_factory=list)
    processing_time_ms:  float     = 0.0