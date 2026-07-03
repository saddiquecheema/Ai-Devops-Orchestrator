# """
# =============================================================================
# backend/services/activity_tracker.py — DAILY ACTIVITY TRACKER
# =============================================================================
# Din bhar ki sari activity in-memory track karta hai.
# End of day report ke liye data provide karta hai.
# Server restart hone pe reset ho jata hai — intentional.
# =============================================================================
# """

# from datetime import datetime
# from typing import Any

# from backend.core.logger import get_logger

# logger = get_logger(__name__)


# class DailyActivityTracker:
#     """Din bhar ki activity ka tracker."""

#     def __init__(self):
#         self._reset()

#     def _reset(self):
#         self.date         = datetime.now().strftime("%B %d, %Y")
#         self.total_prs    = 0
#         self.merged_prs   = 0
#         self.blocked_prs  = 0
#         self.total_pushes = 0
#         self.jira_created = 0
#         self.contributors:  set[str]       = set()
#         self.issues_found:  list[str]      = []
#         self.highlights:    list[str]      = []
#         self.risk_summary:  dict[str, int] = {
#             "low": 0, "medium": 0, "high": 0, "critical": 0
#         }

#     def track_pr_opened(self, pr_number: int | None, author: str | None, repo: str | None) -> None:
#         self.total_prs += 1
#         if author:
#             self.contributors.add(author)

#     def track_pr_merged(self, pr_number: int | None, pr_title: str | None, auto: bool = False) -> None:
#         self.merged_prs += 1
#         num   = pr_number or 0
#         title = (pr_title or "Untitled")[:50]
#         self.highlights.append(f"{'Auto-merged' if auto else 'Merged'}: PR #{num} — {title}")

#     def track_pr_blocked(self, pr_number: int | None, pr_title: str | None, reason: str | None) -> None:
#         self.blocked_prs += 1
#         self.highlights.append(f"Blocked: PR #{pr_number or 0} — {(reason or '')[:60]}")

#     def track_push(self, author: str | None, branch: str | None) -> None:
#         self.total_pushes += 1
#         if author:
#             self.contributors.add(author)

#     def track_risk(self, risk_level: str | None, pr_number: int | None, concerns: list[str] | None) -> None:
#         risk = risk_level or "low"
#         if risk in self.risk_summary:
#             self.risk_summary[risk] += 1
#         if risk in ("high", "critical"):
#             for c in (concerns or [])[:2]:
#                 self.issues_found.append(f"PR #{pr_number or 0}: {c[:80]}")

#     def track_jira_created(self, issue_key: str | None, summary: str | None) -> None:
#         self.jira_created += 1
#         self.highlights.append(f"Issue logged: {issue_key or 'UNKNOWN'} — {(summary or '')[:50]}")

#     def get_report_data(self) -> dict[str, Any]:
#         return {
#             "date":         self.date,
#             "total_prs":    self.total_prs,
#             "merged_prs":   self.merged_prs,
#             "blocked_prs":  self.blocked_prs,
#             "total_pushes": self.total_pushes,
#             "jira_created": self.jira_created,
#             "risk_summary": self.risk_summary,
#             "issues_found": self.issues_found,
#             "contributors": list(self.contributors),
#             "highlights":   self.highlights,
#         }

#     def reset_for_new_day(self) -> None:
#         logger.info("[Tracker] Resetting daily data")
#         self._reset()


# # Singleton
# tracker = DailyActivityTracker()

"""
=============================================================================
app/services/activity_tracker.py — DAILY ACTIVITY TRACKER
=============================================================================
PURPOSE:
  Din bhar ki sari activity track karta hai — memory mein.
  End of day report ke liye data collect karta hai.

TYPE FIXES:
  - Sab parameters Optional accept karte hain (int | None, str | None)
  - Internally safe defaults use hote hain
=============================================================================
"""

from datetime import datetime
from typing import Any

from backend.core.logger import get_logger

logger = get_logger(__name__)


class DailyActivityTracker:
    """
    Din bhar ki activity ka in-memory tracker.
    Server restart hone pe data reset ho jata hai.
    """

    def __init__(self):
        self._reset()

    def _reset(self):
        self.date         = datetime.now().strftime("%B %d, %Y")
        self.total_prs    = 0
        self.merged_prs   = 0
        self.blocked_prs  = 0
        self.total_pushes = 0
        self.jira_created = 0
        self.contributors : set[str]       = set()
        self.issues_found : list[str]      = []
        self.highlights   : list[str]      = []
        self.risk_summary : dict[str, int] = {
            "low": 0, "medium": 0, "high": 0, "critical": 0
        }

    # Fix: int | None aur str | None dono accept karo
    def track_pr_opened(
        self,
        pr_number: int | None,
        author:    str | None,
        repo:      str | None,
    ) -> None:
        self.total_prs += 1
        if author:
            self.contributors.add(author)
        logger.debug(f"[Tracker] PR #{pr_number or 0} opened by {author or 'unknown'}")

    def track_pr_merged(
        self,
        pr_number: int | None,
        pr_title:  str | None,
        auto:      bool = False,
    ) -> None:
        self.merged_prs += 1
        num   = pr_number or 0
        title = (pr_title or "Untitled")[:50]
        label = "Auto-merged" if auto else "Merged"
        self.highlights.append(f"{label}: PR #{num} — {title}")

    def track_pr_blocked(
        self,
        pr_number: int | None,
        pr_title:  str | None,
        reason:    str | None,
    ) -> None:
        self.blocked_prs += 1
        num    = pr_number or 0
        reason = (reason or "Unknown reason")[:60]
        self.highlights.append(f"Blocked: PR #{num} — {reason}")

    def track_push(
        self,
        author: str | None,
        branch: str | None,
    ) -> None:
        self.total_pushes += 1
        if author:
            self.contributors.add(author)

    def track_risk(
        self,
        risk_level: str | None,
        pr_number:  int | None,
        concerns:   list[str] | None,
    ) -> None:
        risk     = risk_level or "low"
        num      = pr_number or 0
        concern_list = concerns or []

        if risk in self.risk_summary:
            self.risk_summary[risk] += 1

        if risk in ("high", "critical"):
            for c in concern_list[:2]:
                self.issues_found.append(f"PR #{num}: {c[:80]}")

    def track_jira_created(
        self,
        issue_key: str | None,
        summary:   str | None,
    ) -> None:
        self.jira_created += 1
        key     = issue_key or "UNKNOWN"
        summary = (summary or "No summary")[:50]
        self.highlights.append(f"Issue logged: {key} — {summary}")

    def get_report_data(self) -> dict[str, Any]:
        return {
            "date":         self.date,
            "total_prs":    self.total_prs,
            "merged_prs":   self.merged_prs,
            "blocked_prs":  self.blocked_prs,
            "total_pushes": self.total_pushes,
            "jira_created": self.jira_created,
            "risk_summary": self.risk_summary,
            "issues_found": self.issues_found,
            "contributors": list(self.contributors),
            "highlights":   self.highlights,
        }

    def reset_for_new_day(self) -> None:
        logger.info("[Tracker] Resetting daily activity data")
        self._reset()


# Singleton
tracker = DailyActivityTracker()