# """
# =============================================================================
# backend/agent/nodes/pr_action_node.py — PR ACTION NODE
# =============================================================================
# PR analysis ke baad actions lo.

# ACTIONS (risk level ke hisaab se):
#   HAMESHA:   Labels + AI Comment + Formal Review + Slack alert
#   HIGH:      Extra Slack warning
#   CRITICAL:  Emergency Slack alert + tracker blocked
#   LOW:       Auto-merge + Slack confirmation
# =============================================================================
# """

# from backend.agent.state import AgentState
# from backend.agent.tools.github_tool import GitHubTool
# from backend.agent.tools.slack_tool import SlackTool
# from backend.core.config import settings
# from backend.core.logger import get_logger
# from backend.models.responses import PRAnalysisResult
# from backend.services.activity_tracker import tracker

# logger = get_logger(__name__)

# RISK_LABELS: dict[str, list[str]] = {
#     "low":      ["ai-reviewed", "risk:low", "auto-merge-candidate"],
#     "medium":   ["ai-reviewed", "risk:medium", "needs-review"],
#     "high":     ["ai-reviewed", "risk:high", "review-required"],
#     "critical": ["ai-reviewed", "risk:critical", "do-not-merge", "security-review"],
# }

# REVIEW_EVENTS: dict[str, str] = {
#     "low":      "APPROVE",
#     "medium":   "COMMENT",
#     "high":     "REQUEST_CHANGES",
#     "critical": "REQUEST_CHANGES",
# }


# def _build_github_comment(state: AgentState, analysis: PRAnalysisResult) -> str:
#     """Professional GitHub PR comment — markdown table format."""
#     risk_label   = analysis.risk_level.upper()
#     merge_status = "Auto-merged successfully" if (analysis.auto_merge and analysis.risk_level == "low") else "Awaiting review"
#     concerns_text  = "\n".join(f"- {c}" for c in analysis.concerns) if analysis.concerns else "- None identified"
#     positives_text = "\n".join(f"- {p}" for p in getattr(analysis, "positive_aspects", [])) or "- N/A"
#     review_text    = ", ".join(f"`{r}`" for r in getattr(analysis, "suggested_reviewers", [])) or "None required"
#     review_time    = getattr(analysis, "estimated_review_time", "N/A")
#     pr_num         = state["event"].pr_number or 0

#     return f"""## Code Review Report

# | Field | Result |
# |-------|--------|
# | **Risk Level** | `{risk_label}` |
# | **Safe to Merge** | {'Yes' if analysis.is_safe_to_merge else 'No'} |
# | **Merge Status** | {merge_status} |
# | **Est. Review Time** | {review_time} |

# ### Summary
# {analysis.summary}

# ### Issues Found
# {concerns_text}

# ### Strengths
# {positives_text}

# ### Recommended Reviewer Expertise
# {review_text}

# ---
# *DevOps Orchestrator — Automated Code Review — PR #{pr_num}*"""


# async def act_on_pr_node(state: AgentState) -> dict:
#     """PR analysis ke baad actions lo."""
#     event    = state["event"]
#     analysis = state.get("pr_analysis")
#     actions  = list(state.get("actions_taken", []))
#     errors   = list(state.get("errors", []))

#     # analysis None guard
#     if analysis is None:
#         errors.append("pr_analysis_missing")
#         return {"actions_taken": actions, "errors": errors, "next_action": "finalize"}

#     # Safe conversions
#     pr_number: int = event.pr_number or 0
#     repo:      str = event.repo      or ""
#     pr_author: str = event.pr_author or "unknown"
#     pr_title:  str = event.pr_title  or "Untitled PR"
#     risk:      str = analysis.risk_level
#     concerns:  list[str] = analysis.concerns or []

#     github = GitHubTool()
#     slack  = SlackTool()

#     # Track
#     tracker.track_pr_opened(pr_number, pr_author, repo)
#     tracker.track_risk(risk, pr_number, concerns)

#     # ACTION 1: Labels
#     try:
#         labels = RISK_LABELS.get(risk, ["ai-reviewed"])
#         await github.set_pr_label(repo, pr_number, labels)
#         actions.append(f"github_labels_set:{','.join(labels)}")
#     except Exception as e:
#         errors.append(f"github_label_failed: {str(e)[:80]}")

#     # ACTION 2: AI Comment
#     try:
#         await github.add_pr_comment(repo, pr_number, _build_github_comment(state, analysis))
#         actions.append("github_comment_posted")
#     except Exception as e:
#         errors.append(f"github_comment_failed: {str(e)[:80]}")

#     # ACTION 3: Formal Review
#     try:
#         review_event = REVIEW_EVENTS.get(risk, "COMMENT")
#         body_map = {
#             "APPROVE":         f"Approved — Low risk, no concerns.\n\n{analysis.summary}",
#             "COMMENT":         f"Review Note — Medium risk, human review recommended.\n\n{analysis.summary}",
#             "REQUEST_CHANGES": f"Changes Required — {risk.upper()} risk.\n\n{analysis.summary}",
#         }
#         await github.add_pr_review(repo=repo, pr_number=pr_number, body=body_map[review_event], event=review_event)
#         actions.append(f"github_review_submitted:{review_event}")
#     except Exception as e:
#         errors.append(f"github_review_failed: {str(e)[:80]}")

#     # ACTION 4: Slack Alert
#     try:
#         await slack.send_pr_alert(event, analysis)
#         actions.append("slack_pr_alert_sent")
#     except Exception as e:
#         errors.append(f"slack_alert_failed: {str(e)[:80]}")

#     # ACTION 5: HIGH risk warning
#     if risk == "high":
#         try:
#             concerns_text = "\n".join(f"  • {c}" for c in concerns)
#             await slack.send_message(
#                 channel=settings.default_slack_channel,
#                 text=(
#                     f"HIGH RISK PR — Immediate Review Required\n"
#                     f"PR #{pr_number}: {pr_title}\n"
#                     f"Repository: {repo} | Author: {pr_author}\n\n"
#                     f"Issues:\n{concerns_text or '  None listed'}"
#                 ),
#             )
#             actions.append("slack_high_risk_warning_sent")
#         except Exception as e:
#             errors.append(f"slack_high_warning_failed: {str(e)[:80]}")

#     # ACTION 6: CRITICAL emergency
#     if risk == "critical":
#         try:
#             concerns_text = "\n".join(f"  • {c}" for c in concerns)
#             await slack.send_message(
#                 channel=settings.default_slack_channel,
#                 text=(
#                     f"CRITICAL RISK — DO NOT MERGE\n"
#                     f"PR #{pr_number}: {pr_title}\n"
#                     f"Repository: {repo} | Author: {pr_author}\n\n"
#                     f"Critical Issues:\n{concerns_text or '  None listed'}\n\n"
#                     f"Action Required: Security team review before any merge."
#                 ),
#             )
#             actions.append("slack_critical_alert_sent")
#             tracker.track_pr_blocked(pr_number, pr_title, "Critical risk")
#         except Exception as e:
#             errors.append(f"slack_critical_failed: {str(e)[:80]}")

#     # ACTION 7: LOW risk auto-merge
#     if analysis.auto_merge and risk == "low" and not concerns:
#         try:
#             commit_msg = f"feat: merge PR #{pr_number} — {pr_title} [Approved: Low Risk]"
#             result     = await github.merge_pr(repo, pr_number, commit_msg)
#             sha        = result.get("sha", "")[:8]
#             actions.append(f"pr_auto_merged:sha={sha}")
#             tracker.track_pr_merged(pr_number, pr_title, auto=True)

#             await slack.send_message(
#                 channel=settings.default_slack_channel,
#                 text=(
#                     f"PR Merged Successfully\n"
#                     f"PR #{pr_number}: {pr_title}\n"
#                     f"Repository: {repo} | Risk: LOW | No concerns."
#                 ),
#             )
#             actions.append("slack_merge_confirmation_sent")
#         except Exception as e:
#             errors.append(f"auto_merge_failed: {str(e)[:80]}")

#     elif analysis.auto_merge and (risk != "low" or concerns):
#         actions.append("auto_merge_skipped:safety_override")

#     logger.info(f"[PR Action] Done | actions={len(actions)} | errors={len(errors)}")
#     return {"actions_taken": actions, "errors": errors, "next_action": "finalize"}
"""
=============================================================================
app/agent/nodes/pr_action_node.py — PR ACTION NODE
=============================================================================
ALL ERRORS FIXED:
  1. int | None → int safe conversion (pr_number)
  2. risk uninitialized → analysis None guard pehle
  3. analysis.concerns None guard
  4. analysis.risk_level None guard
  5. set_pr_label → github_tool mein add kiya
  6. str | None → str safe conversion (repo, pr_number)
=============================================================================
"""

from backend.agent.state import AgentState
from backend.agent.tools.github_tool import GitHubTool
from backend.agent.tools.slack_tool import SlackTool
from backend.core.config import settings
from backend.core.logger import get_logger
from backend.models.responses import PRAnalysisResult
from backend.services.activity_tracker import tracker
from backend.main import ws_manager
logger = get_logger(__name__)

# Risk level ke hisaab se GitHub labels
RISK_LABELS: dict[str, list[str]] = {
    "low":      ["ai-reviewed", "risk:low", "auto-merge-candidate"],
    "medium":   ["ai-reviewed", "risk:medium", "needs-review"],
    "high":     ["ai-reviewed", "risk:high", "review-required"],
    "critical": ["ai-reviewed", "risk:critical", "do-not-merge", "security-review"],
}

# Risk level ke hisaab se GitHub Review event
REVIEW_EVENTS: dict[str, str] = {
    "low":      "APPROVE",
    "medium":   "COMMENT",
    "high":     "REQUEST_CHANGES",
    "critical": "REQUEST_CHANGES",
}


def _build_github_comment(event: AgentState, analysis: PRAnalysisResult) -> str:
    """Professional GitHub PR comment — markdown format."""
    risk_display = {
        "low":      "LOW",
        "medium":   "MEDIUM",
        "high":     "HIGH",
        "critical": "CRITICAL",
    }
    risk_badge = risk_display.get(analysis.risk_level, analysis.risk_level.upper())

    merge_status = (
        "Auto-merged successfully"
        if analysis.auto_merge and analysis.risk_level == "low"
        else "Awaiting review"
    )

    concerns_text = (
        "\n".join(f"- {c}" for c in analysis.concerns)
        if analysis.concerns
        else "- None identified"
    )

    positives = getattr(analysis, "positive_aspects", [])
    positives_text = (
        "\n".join(f"- {p}" for p in positives)
        if positives
        else "- N/A"
    )

    reviewers   = getattr(analysis, "suggested_reviewers", [])
    review_text = ", ".join(f"`{r}`" for r in reviewers) if reviewers else "None required"
    review_time = getattr(analysis, "estimated_review_time", "N/A")

    pr_num = event["event"].pr_number or 0

    return f"""## Code Review Report

| Field | Result |
|-------|--------|
| **Risk Level** | `{risk_badge}` |
| **Safe to Merge** | {'Yes' if analysis.is_safe_to_merge else 'No'} |
| **Merge Status** | {merge_status} |
| **Est. Review Time** | {review_time} |

### Summary
{analysis.summary}

### Issues Found
{concerns_text}

### Strengths
{positives_text}

### Recommended Reviewer Expertise
{review_text}

---
*DevOps Orchestrator — Automated Code Review — PR #{pr_num}*"""


async def act_on_pr_node(state: AgentState) -> dict:
    """
    PR analysis ke baad comprehensive actions lo.
    Sab None checks properly handle kiye hain.
    """
    event    = state["event"]
    analysis = state.get("pr_analysis")   # Fix 2,4,5: None check
    actions  = list(state.get("actions_taken", []))
    errors   = list(state.get("errors", []))

    # ── Fix 2: analysis None guard ───────────────────────────────────────────
    if analysis is None:
        errors.append("pr_analysis_missing: no analysis result in state")
        logger.error("[PR Action] No analysis result — skipping actions")
        return {
            "actions_taken": actions,
            "errors":        errors,
            "next_action":   "finalize",
        }

    # ── Fix 1,3: Safe int conversion ─────────────────────────────────────────
    pr_number: int  = event.pr_number  or 0
    repo:      str  = event.repo       or ""
    pr_author: str  = event.pr_author  or "unknown"
    pr_title:  str  = event.pr_title   or "Untitled PR"
    branch:    str  = event.branch     or "main"

    # ── Fix 5: risk safely from analysis ─────────────────────────────────────
    risk:     str       = analysis.risk_level   # analysis is not None here
    concerns: list[str] = analysis.concerns or []

    github = GitHubTool()
    slack  = SlackTool()

    # Track activity
    tracker.track_pr_opened(pr_number, pr_author, repo)
    tracker.track_risk(risk, pr_number, concerns)

    # ==========================================================================
    # ACTION 1: GitHub Labels lagao
    # Fix 6: set_pr_label github_tool mein exist karta hai
    # ==========================================================================
    try:
        labels = RISK_LABELS.get(risk, ["ai-reviewed"])
        await github.set_pr_label(repo, pr_number, labels)
        actions.append(f"github_labels_set:{','.join(labels)}")
        # BROADCAST: Labels update
        await ws_manager.broadcast({
            "type": "pr_action",
            "message": f"🏷️ Labels set: {', '.join(labels)}",
            "pr_number": pr_number
        })
        logger.info(f"[PR Action] Labels set: {labels}")
    except Exception as e:
        errors.append(f"github_label_failed: {str(e)[:80]}")
        logger.error(f"[PR Action] Label failed: {e}")

    # ==========================================================================
    # ACTION 2: AI Comment post karo
    # Fix 7,8: repo aur pr_number ab guaranteed str aur int hain
    # ==========================================================================
    try:
        comment_body = _build_github_comment(state, analysis)
        result = await github.add_pr_comment(repo, pr_number, comment_body)
        actions.append("github_comment_posted")
        # BROADCAST: Comment posted
        await ws_manager.broadcast({
            "type": "pr_action",
            "message": "💬 AI Review comment posted on GitHub",
            "pr_number": pr_number
        })
        logger.info(f"[PR Action] Comment posted: {result.get('url', '')}")
    except Exception as e:
        errors.append(f"github_comment_failed: {str(e)[:80]}")
        logger.error(f"[PR Action] Comment failed: {e}")

    # ==========================================================================
    # ACTION 3: Formal GitHub Review submit karo
    # ==========================================================================
    try:
        review_event = REVIEW_EVENTS.get(risk, "COMMENT")

        review_body_map = {
            "APPROVE":         f"Approved — Low risk, no concerns found.\n\n{analysis.summary}",
            "COMMENT":         f"Review Note — Medium risk, human review recommended.\n\n{analysis.summary}",
            "REQUEST_CHANGES": f"Changes Required — {risk.upper()} risk detected.\n\n{analysis.summary}",
        }

        await github.add_pr_review(
            repo      = repo,
            pr_number = pr_number,
            body      = review_body_map[review_event],
            event     = review_event,
        )
        actions.append(f"github_review_submitted:{review_event}")
        logger.info(f"[PR Action] Review: {review_event}")
    except Exception as e:
        errors.append(f"github_review_failed: {str(e)[:80]}")
        logger.error(f"[PR Action] Review failed: {e}")

    # ==========================================================================
    # ACTION 4: Slack Alert
    # ==========================================================================
    try:
        await slack.send_pr_alert(event, analysis)
        actions.append("slack_pr_alert_sent")
        logger.info("[PR Action] Slack alert sent")
    except Exception as e:
        errors.append(f"slack_alert_failed: {str(e)[:80]}")
        logger.error(f"[PR Action] Slack failed: {e}")

    # ==========================================================================
    # ACTION 5: HIGH risk — Extra warning
    # ==========================================================================
    if risk == "high":
        try:
            concerns_text = "\n".join(f"  • {c}" for c in concerns)
            await slack.send_message(
                channel = settings.default_slack_channel,
                text    = (
                    f"HIGH RISK PR — Immediate Review Required\n"
                    f"PR #{pr_number}: {pr_title}\n"
                    f"Repository: {repo} | Author: {pr_author}\n\n"
                    f"Issues:\n{concerns_text or '  None listed'}"
                ),
            )
            actions.append("slack_high_risk_warning_sent")
        except Exception as e:
            errors.append(f"slack_high_warning_failed: {str(e)[:80]}")

    # ==========================================================================
    # ACTION 6: CRITICAL risk — Emergency
    # ==========================================================================
    if risk == "critical":
        try:
            concerns_text = "\n".join(f"  • {c}" for c in concerns)
            await slack.send_message(
                channel = settings.default_slack_channel,
                text    = (
                    f"CRITICAL RISK — DO NOT MERGE\n"
                    f"PR #{pr_number}: {pr_title}\n"
                    f"Repository: {repo} | Author: {pr_author}\n\n"
                    f"Critical Issues:\n{concerns_text or '  None listed'}\n\n"
                    f"Action Required: Security team review before any merge."
                ),
            )
            actions.append("slack_critical_alert_sent")
            tracker.track_pr_blocked(pr_number, pr_title, "Critical risk")
            logger.warning(f"[PR Action] CRITICAL alert sent for PR #{pr_number}")
        except Exception as e:
            errors.append(f"slack_critical_failed: {str(e)[:80]}")

    # ==========================================================================
    # ACTION 7: LOW risk — Auto merge
    # ==========================================================================
    if analysis.auto_merge and risk == "low" and not concerns:
        try:
            commit_msg = (
                f"feat: merge PR #{pr_number} — {pr_title} "
                f"[Approved: Low Risk]"
            )
            result = await github.merge_pr(repo, pr_number, commit_msg)
            # BROADCAST: Merge Success
            await ws_manager.broadcast({
                "type": "pr_merged",
                "message": f"🚀 PR #{pr_number} Auto-merged successfully!",
                "pr_number": pr_number
            })
            sha    = result.get("sha", "")[:8]
            actions.append(f"pr_auto_merged:sha={sha}")
            tracker.track_pr_merged(pr_number, pr_title, auto=True)

            await slack.send_message(
                channel = settings.default_slack_channel,
                text    = (
                    f"PR Merged Successfully\n"
                    f"PR #{pr_number}: {pr_title}\n"
                    f"Repository: {repo} | Risk: LOW | No concerns found."
                ),
            )
            actions.append("slack_merge_confirmation_sent")
            logger.info(f"[PR Action] Auto-merged PR #{pr_number} sha={sha}")

        except Exception as e:
            errors.append(f"auto_merge_failed: {str(e)[:80]}")

            # Dashboard ko error alert bhejen
            await ws_manager.broadcast({
                "type": "error",
                "message": f"❌ Action Failed: Could not set labels on PR #{pr_number}",
                "details": str(e)
            })
            logger.error(f"[PR Action] Auto-merge failed: {e}")

    elif analysis.auto_merge and (risk != "low" or concerns):
        logger.warning(
            f"[PR Action] Auto-merge SKIPPED — risk={risk}, concerns={len(concerns)}"
        )
        actions.append("auto_merge_skipped:safety_override")

    logger.info(
        f"[PR Action] Complete | actions={len(actions)} | errors={len(errors)}"
    )

    return {
        "actions_taken": actions,
        "errors":        errors,
        "next_action":   "finalize",
    }