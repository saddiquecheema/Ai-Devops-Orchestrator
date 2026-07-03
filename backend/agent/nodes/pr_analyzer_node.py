# """
# =============================================================================
# backend/agent/nodes/pr_analyzer_node.py — PR ANALYZER NODE
# =============================================================================
# PR ko AI se analyze karo.
# Ye sabse important node hai — yahan actual AI magic hoti hai.

# STEPS:
#   1. GitHub se PR diff + files + commits fetch karo
#   2. Sensitive files auto-detect
#   3. Rich prompt banao
#   4. Groq LLM call karo
#   5. JSON parse → PRAnalysisResult
# =============================================================================
# """

# import json

# from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
# from langchain_groq import ChatGroq

# from backend.agent.state import AgentState
# from backend.agent.tools.github_tool import GitHubTool
# from backend.core.config import settings
# from backend.core.logger import get_logger
# from backend.models.responses import PRAnalysisResult

# logger = get_logger(__name__)

# SYSTEM_PROMPT = """You are a Principal DevOps Engineer and Security-Aware Code Reviewer with 15+ years of experience.

# Analyze the Pull Request and return ONLY this JSON object — no markdown, no extra text:
# {
#   "is_safe_to_merge": true or false,
#   "risk_level": "low" or "medium" or "high" or "critical",
#   "summary": "2-3 sentences: what this PR does",
#   "concerns": ["specific concern 1", "specific concern 2"],
#   "positive_aspects": ["good thing 1"],
#   "suggested_reviewers": ["backend engineer"],
#   "auto_merge": true or false,
#   "requires_tests": true or false,
#   "estimated_review_time": "5 mins" or "30 mins" or "2 hours"
# }

# RISK RULES:
#   low      → docs, tests, README only    → auto_merge: true if no concerns
#   medium   → new features with tests     → auto_merge: false
#   high     → auth, DB, breaking changes  → auto_merge: false
#   critical → secrets, infra, .env/.key   → auto_merge: false, block merge

# SENSITIVE FILE RULES:
#   Any sensitive file → minimum risk: high
#   .env/.key/.pem/secrets → risk: critical

# AUTO MERGE (strict):
#   true ONLY when: risk=low AND concerns=[] AND no sensitive files
#   false in all other cases

# Return ONLY the JSON. Nothing else."""


# def _clean_llm_json(raw: str) -> str:
#     """LLM response se pure JSON extract karo."""
#     raw = raw.strip()
#     if raw.startswith("```"):
#         parts = raw.split("```")
#         raw = parts[1] if len(parts) > 1 else raw
#         if raw.startswith("json"):
#             raw = raw[4:]
#     start = raw.find("{")
#     end   = raw.rfind("}") + 1
#     if start != -1 and end > start:
#         raw = raw[start:end]
#     return raw.strip()


# def _build_prompt(event, diff_data: dict, commits: list[dict]) -> str:
#     """Rich LLM prompt banao."""
#     commit_lines = "\n".join(
#         f"  [{c['sha']}] {c['author']}: {c['message']}" for c in commits[:10]
#     ) or "  No commits available"

#     files_summary = "\n".join(
#         f"  [{f['status'].upper():8}] {f['filename']} (+{f['additions']}/-{f['deletions']})"
#         for f in diff_data.get("changed_files", [])[:20]
#     ) or "  No file details available"

#     sensitive = diff_data.get("sensitive_files", [])
#     sensitive_warning = (
#         "\n⚠️  SENSITIVE FILES:\n" + "\n".join(f"  🔴 {f}" for f in sensitive)
#         if sensitive else "\n✅ No sensitive files"
#     )

#     truncation = "\n[Diff truncated to 8000 chars]" if diff_data.get("diff_truncated") else ""

#     return f"""=== PULL REQUEST ===
# PR #{event.pr_number}: {diff_data['title']}
# Author: {diff_data['author']}
# Branch: {diff_data['head_branch']} → {diff_data['base_branch']}

# === STATS ===
# Files: {diff_data['files_changed']} | +{diff_data['additions']} / -{diff_data['deletions']} | Commits: {diff_data['commits']}
# {sensitive_warning}

# === DESCRIPTION ===
# {diff_data['body']}

# === COMMITS ===
# {commit_lines}

# === CHANGED FILES ===
# {files_summary}

# === DIFF ==={truncation}
# {diff_data['diff']}"""


# async def analyze_pr_node(state: AgentState) -> dict:
#     """PR ko AI se analyze karo."""
#     event  = state["event"]
#     errors = list(state.get("errors", []))

#     try:
#         github = GitHubTool()

#         # Step 1: PR data fetch
#         logger.info(f"[PR Analyzer] Fetching: {event.repo} #{event.pr_number}")
#         diff_data = await github.get_pr_diff(event.repo, event.pr_number)

#         if diff_data["sensitive_files"]:
#             logger.warning(f"[PR Analyzer] Sensitive files: {diff_data['sensitive_files']}")

#         # Step 2: Commits fetch
#         try:
#             commits = await github.get_pr_commit_history(event.repo, event.pr_number)
#         except Exception as e:
#             logger.warning(f"[PR Analyzer] Commits fetch failed (non-fatal): {e}")
#             commits = []

#         # Step 3: LLM call
#         user_prompt = _build_prompt(event, diff_data, commits)
#         messages    = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)]

#         logger.info(f"[PR Analyzer] Calling Groq | files={diff_data['files_changed']}")

#         llm      = ChatGroq(api_key=settings.groq_api_key, model=settings.groq_model,
#                             temperature=settings.llm_temperature, max_tokens=settings.llm_max_tokens)
#         response = await llm.ainvoke(messages)
#         raw_json = response.content if isinstance(response.content, str) else str(response.content)

#         # Step 4: Parse
#         clean_json    = _clean_llm_json(raw_json)
#         analysis_dict = json.loads(clean_json)
#         analysis      = PRAnalysisResult(**analysis_dict)

#         # Safety: sensitive files → force auto_merge=False
#         if diff_data["sensitive_files"] and analysis.auto_merge:
#             logger.warning("[PR Analyzer] Safety override: auto_merge=False (sensitive files)")
#             analysis = PRAnalysisResult(**{**analysis_dict, "auto_merge": False, "risk_level": "high"})

#         logger.info(
#             f"[PR Analyzer] Done | risk={analysis.risk_level} | "
#             f"safe={analysis.is_safe_to_merge} | auto_merge={analysis.auto_merge}"
#         )

#         return {
#             "pr_analysis":   analysis,
#             "actions_taken": state.get("actions_taken", []) + ["pr_analyzed"],
#             "messages":      [AIMessage(content=clean_json)],
#             "next_action":   "act_on_pr",
#         }

#     except json.JSONDecodeError as e:
#         msg = f"LLM invalid JSON: {e}"
#         logger.error(f"[PR Analyzer] {msg}")
#         return {"errors": errors + [msg], "next_action": "handle_error"}

#     except Exception as e:
#         msg = f"PR analysis failed: {str(e)}"
#         logger.error(f"[PR Analyzer] {msg}")
#         return {"errors": errors + [msg], "next_action": "handle_error"}



"""
=============================================================================
app/agent/nodes/pr_analyzer_node.py — PR ANALYZER NODE
=============================================================================
PURPOSE:
  Pull Request ko AI se deeply analyze karo.
  Ye node sabse important node hai — yahan actual AI magic hoti hai.

ENHANCED ANALYSIS:
  Basic version sirf diff dekhta tha.
  Is enhanced version mein:
    - Commit history bhi analyze hoti hai
    - Sensitive files automatically detect hoti hain
    - LLM ko zyada context milta hai → better decisions
    - Detailed scoring system (0-100) har category ke liye

STEPS:
  1. GitHub se PR diff + files + commits fetch karo
  2. Sensitive files automatically detect karo
  3. Sab data ek rich prompt mein compile karo
  4. Groq LLM ko bhejo — detailed JSON response maango
  5. Response validate karo → PRAnalysisResult mein convert karo
=============================================================================
"""

import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from backend.agent.state import AgentState
from backend.agent.tools.github_tool import GitHubTool
from backend.core.config import settings
from backend.core.logger import get_logger
from backend.models.responses import PRAnalysisResult
from backend.main import ws_manager
from backend.agent.nodes.summarize_node import generate_ai_summary

logger = get_logger(__name__)


# =============================================================================
# LLM SYSTEM PROMPT — Enhanced Version
# =============================================================================
# Ye prompt carefully engineered hai taake LLM:
#   1. Senior DevOps engineer ki tarah soche
#   2. Consistent JSON return kare
#   3. Sensitive files pe extra attention de
#   4. Auto-merge ke liye strict rules follow kare
# =============================================================================

SYSTEM_PROMPT = """You are a Principal DevOps Engineer and Security-Aware Code Reviewer with 15+ years of experience.

Your job is to review a Pull Request and return a structured JSON risk assessment.

RETURN ONLY this JSON object — no markdown, no explanation, no extra text:
{
  "is_safe_to_merge": true or false,
  "risk_level": "low" or "medium" or "high" or "critical",
  "summary": "2-3 clear sentences: what this PR does and why it matters",
  "concerns": ["specific concern 1", "specific concern 2"],
  "positive_aspects": ["good thing 1", "good thing 2"],
  "suggested_reviewers": ["backend engineer", "security specialist"],
  "auto_merge": true or false,
  "requires_tests": true or false,
  "estimated_review_time": "5 mins" or "30 mins" or "2 hours"
}

=== RISK LEVEL RULES ===
low:
  - Only documentation, comments, or README changes
  - Only test file additions/modifications
  - Minor UI text/copy changes
  - Trivial config value updates (NOT secret changes)
  → auto_merge: true ONLY if concerns array is EMPTY

medium:
  - New feature with proper test coverage
  - Non-breaking refactoring with tests
  - Dependency updates (minor versions)
  - Adding new API endpoints (non-breaking)
  → auto_merge: false, human review recommended

high:
  - Authentication or authorization logic changes
  - Database schema changes or migrations
  - Breaking API changes
  - Core business logic modifications
  - Dependency major version upgrades
  → auto_merge: false, mandatory human review

critical:
  - Any change to .env, secrets, credentials, or API keys
  - Production infrastructure config (Dockerfile, nginx, CI/CD)
  - Security-sensitive files (.pem, .key, certificates)
  - Core payment or financial logic
  - Admin/superuser permission changes
  → auto_merge: false, BLOCK merge until security team reviews

=== SENSITIVE FILE BONUS RULES ===
If sensitive_files list is NOT empty → minimum risk_level is "high"
If sensitive_files contains .env, .key, .pem, secrets → risk_level MUST be "critical"

=== AUTO MERGE RULES (STRICT) ===
auto_merge = true ONLY when ALL of these are true:
  1. risk_level is exactly "low"
  2. concerns array is completely empty []
  3. sensitive_files list is empty
  4. No security-related keywords in diff (password, secret, token, key, auth)
auto_merge = false in ALL other cases — when in doubt, set false

Return ONLY the JSON. Nothing else."""


def _clean_llm_json(raw: str) -> str:
    """
    LLM response se pure JSON extract karo.
    LLM kabhi kabhi markdown code blocks mein wrap karta hai.
    """
    raw = raw.strip()

    # ``` blocks remove karo
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]

    # Pehla { aur aakhri } ke beech ka content lo
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    return raw.strip()


def _build_analysis_prompt(event, diff_data: dict, commits: list[dict]) -> str:
    """
    LLM ke liye rich context prompt banao.
    Jitna zyada context → utna better AI decision.
    """
    # Commit messages format karo
    commit_lines = "\n".join(
        f"  [{c['sha']}] {c['author']}: {c['message']}"
        for c in commits[:10]
    ) or "  No commits data available"

    # Changed files format karo
    files_summary = "\n".join(
        f"  [{f['status'].upper():8}] {f['filename']} (+{f['additions']}/-{f['deletions']})"
        for f in diff_data.get("changed_files", [])[:20]
    ) or "  No file details available"

    # Sensitive files warning
    sensitive = diff_data.get("sensitive_files", [])
    sensitive_warning = (
        f"\n⚠️  SENSITIVE FILES DETECTED:\n" +
        "\n".join(f"  🔴 {f}" for f in sensitive)
        if sensitive else
        "\n✅ No sensitive files detected"
    )

    # Diff truncation notice
    truncation_note = (
        "\n[Note: Diff truncated to 8000 chars — full diff may contain more changes]"
        if diff_data.get("diff_truncated") else ""
    )

    return f"""=== PULL REQUEST DETAILS ===
PR #{event.pr_number}: {diff_data['title']}
URL: {diff_data.get('pr_url', 'N/A')}
Author: {diff_data['author']}
Branch: {diff_data['head_branch']} → {diff_data['base_branch']}

=== CHANGE STATISTICS ===
Files Changed : {diff_data['files_changed']}
Additions     : +{diff_data['additions']} lines
Deletions     : -{diff_data['deletions']} lines
Total Commits : {diff_data['commits']}
{sensitive_warning}

=== PR DESCRIPTION ===
{diff_data['body']}

=== COMMIT HISTORY ===
{commit_lines}

=== CHANGED FILES ===
{files_summary}

=== CODE DIFF ==={truncation_note}
{diff_data['diff']}"""


async def analyze_pr_node(state: AgentState) -> dict:
    """
    PR ko AI se comprehensively analyze karo.

    Enhanced Flow:
      1. Diff + Files fetch (get_pr_diff — 3 API calls internally)
      2. Commit history fetch (get_pr_commit_history)
      3. Rich prompt compile karo (sensitive files, stats, history)
      4. Groq LLM call karo
      5. JSON validate + PRAnalysisResult banao

    Success: state["pr_analysis"] = PRAnalysisResult, next = "act_on_pr"
    Failure: state["errors"] updated, next = "handle_error"
    """
    event  = state["event"]
    errors = list(state.get("errors", []))

    try:
        github = GitHubTool()

        # ── Step 1: PR diff + files + sensitive file detection ──────────────
        logger.info(
            f"[PR Analyzer] Fetching PR data: {event.repo} #{event.pr_number}"
        )
        diff_data = await github.get_pr_diff(event.repo, event.pr_number)

        # Sensitive files early warning log
        if diff_data["sensitive_files"]:
            logger.warning(
                f"[PR Analyzer] ⚠️ Sensitive files in PR #{event.pr_number}: "
                f"{diff_data['sensitive_files']}"
            )

        # ── Step 2: Commit history fetch karo ───────────────────────────────
        logger.info(f"[PR Analyzer] Fetching commit history...")
        try:
            commits = await github.get_pr_commit_history(event.repo, event.pr_number)
        except Exception as e:
            logger.warning(f"[PR Analyzer] Commit history fetch failed (non-fatal): {e}")
            commits = []

        # ── Step 3: LLM prompt banao ─────────────────────────────────────────
        user_prompt = _build_analysis_prompt(event, diff_data, commits)

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        # ── Step 4: Groq LLM call karo ──────────────────────────────────────
        logger.info(
            f"[PR Analyzer] Calling Groq ({settings.groq_model}) | "
            f"files={diff_data['files_changed']} | "
            f"sensitive={len(diff_data['sensitive_files'])}"
        )

        llm = ChatGroq(
            api_key     = settings.groq_api_key,
            model       = settings.groq_model,
            temperature = settings.llm_temperature,
            max_tokens  = settings.llm_max_tokens,
        )
        response  = await llm.ainvoke(messages)
        raw_json  = response.content

        # ── Step 5: JSON parse + validate karo ──────────────────────────────
        clean_json    = _clean_llm_json(raw_json)
        analysis_dict = json.loads(clean_json)

        # PRAnalysisResult mein convert karo (Pydantic validation)
        analysis = PRAnalysisResult(**analysis_dict)

        # --- NAYA: AI Summary Generation for State ---
        ai_summary = await generate_ai_summary(analysis.summary, context="Pull Request")

        # Safety override: agar sensitive files hain toh auto_merge FORCE False
        if diff_data["sensitive_files"] and analysis.auto_merge:
            logger.warning(
                "[PR Analyzer] Safety override: auto_merge forced False "
                "due to sensitive files"
            )
            analysis = PRAnalysisResult(
                **{**analysis_dict, "auto_merge": False, "risk_level": "high"}
            )

        # --- MERA UPDATE: DASHBOARD BROADCAST ---
        await ws_manager.broadcast({
            "type": "analysis_result",
            "pr_number": event.pr_number,
            "risk_level": analysis.risk_level,
            "message": f"🧠 PR #{event.pr_number} Analyzed: Risk Level {analysis.risk_level.upper()}",
            # "summary": analysis.summary[:100] + "..." if len(analysis.summary) > 100 else analysis.summary
            "summary": ai_summary
        })

        logger.info(
            f"[PR Analyzer] Analysis complete. Summary: {ai_summary}",
            f"risk={analysis.risk_level} | ",
            f"safe={analysis.is_safe_to_merge} | ",
            f"auto_merge={analysis.auto_merge} | ",
            f"concerns={len(analysis.concerns)}",
        )

        return {
            "pr_analysis":   analysis,
            "analysis_summary": ai_summary,
            "actions_taken": state.get("actions_taken", []) + ["pr_analyzed"],
            "messages":      [AIMessage(content=clean_json)],
            "next_action":   "act_on_pr",
        }

    except json.JSONDecodeError as e:
        msg = f"LLM invalid JSON response: {e}"
        logger.error(f"[PR Analyzer] {msg}")
        errors.append(msg)
        return {"errors": errors, "next_action": "handle_error"}

    except Exception as e:
        msg = f"PR analysis failed: {str(e)}"
        logger.error(f"[PR Analyzer] {msg}")
        # Dashboard ko error ka signal bhejen
        await ws_manager.broadcast({
            "type": "error_alert",
            "message": f"❌ Analysis Failed for PR #{event.pr_number}",
            "details": str(e)
        })
        errors.append(msg)
        return {"errors": errors, "next_action": "handle_error"}