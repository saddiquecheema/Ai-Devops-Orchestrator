# """
# =============================================================================
# backend/agent/nodes/jira_creator_node.py — JIRA ISSUE CREATOR NODE
# =============================================================================
# Slack message → Jira ticket → Slack confirmation card.

# TRIGGER KEYWORDS:
#   "bug: ..."    → Bug, High priority
#   "issue: ..."  → Task, Medium priority
#   "task: ..."   → Task, Medium priority
#   "create: ..." → Task, Medium priority
#   "ticket: ..." → Story, Medium priority

# STEPS:
#   1. Slack User ID → Real name (Slack API)
#   2. LLM se message parse karo → structured JSON
#   3. Jira mein ticket create karo
#   4. Slack pe rich confirmation card bhejo
# =============================================================================
# """

# import json
# from typing import Any

# from langchain_core.messages import HumanMessage, SystemMessage
# from langchain_groq import ChatGroq

# from backend.agent.state import AgentState
# from backend.agent.tools.jira_tool import JiraTool
# from backend.agent.tools.slack_tool import SlackTool
# from backend.core.config import settings
# from backend.core.logger import get_logger
# from backend.models.responses import JiraIssuePayload
# from backend.services.activity_tracker import tracker

# logger = get_logger(__name__)

# SYSTEM_PROMPT = """You are a project manager assistant creating Jira tickets.

# Extract issue details from the Slack message and return ONLY this JSON:
# {
#   "summary": "Clear, actionable title (max 100 chars, start with verb)",
#   "description": "Detailed: what happened, where, expected vs actual",
#   "issue_type": "Bug" or "Task" or "Story",
#   "priority": "Highest" or "High" or "Medium" or "Low" or "Lowest",
#   "labels": ["frontend", "backend", "database", "auth", "ui", "api", "mobile"]
# }

# Priority guide:
#   Highest → Production down, data loss, security breach
#   High    → Major feature broken, blocking users
#   Medium  → Feature not working, workaround exists
#   Low     → Minor issue, cosmetic
#   Lowest  → Enhancement, nice to have

# Return ONLY the JSON. No markdown, no explanation."""


# async def _get_slack_display_name(user_id: str) -> str:
#     """
#     Slack User ID (U0B4Q6JBZAQ) → Real Name (Inam ur Rehman).
#     Fail ho toh user_id return karo — graceful fallback.
#     """
#     if not user_id or not user_id.startswith("U"):
#         return user_id or "unknown"

#     try:
#         import httpx
#         async with httpx.AsyncClient(timeout=10.0) as client:
#             resp = await client.get(
#                 f"{settings.slack_api_url}/users.info",
#                 headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
#                 params={"user": user_id},
#             )
#             data = resp.json()
#             if data.get("ok"):
#                 user    = data.get("user", {})
#                 profile = user.get("profile", {})
#                 return (
#                     profile.get("real_name")
#                     or profile.get("display_name")
#                     or user.get("name")
#                     or user_id
#                 )
#     except Exception:
#         pass

#     return user_id


# def _clean_json(raw: Any) -> str:
#     """LLM response se pure JSON extract karo."""
#     if raw is None:
#         raise ValueError("Empty response from LLM")

#     text = raw if isinstance(raw, str) else str(raw)
#     text = text.strip()

#     if not text:
#         raise ValueError("Empty response from LLM")

#     if text.startswith("```"):
#         parts = text.split("```")
#         text = parts[1] if len(parts) > 1 else text
#         if text.startswith("json"):
#             text = text[4:]

#     start = text.find("{")
#     end   = text.rfind("}") + 1
#     if start != -1 and end > start:
#         text = text[start:end]

#     return text.strip()


# def _classify_error(error: Exception) -> tuple[str, str, str]:
#     """Error classify karo → (type, short_msg, detail)."""
#     err_str = str(error).lower()

#     if isinstance(error, (json.JSONDecodeError, ValueError, KeyError)) or \
#        any(k in err_str for k in ("json", "parse", "expecting", "decode", "empty response")):
#         return (
#             "ParseError",
#             "LLM returned invalid response",
#             f"AI model ka response parse nahi ho saka. Detail: {str(error)[:150]}",
#         )
#     elif "401" in err_str or "403" in err_str or "auth" in err_str:
#         return (
#             "AuthError",
#             "Jira authentication failed",
#             f"JIRA_EMAIL aur JIRA_API_TOKEN check karo. Detail: {str(error)[:150]}",
#         )
#     elif "404" in err_str:
#         return (
#             "APIError",
#             "Jira project not found",
#             f"JIRA_PROJECT_KEY '{settings.jira_project_key}' check karo.",
#         )
#     elif any(k in err_str for k in ("timeout", "connect", "network")):
#         return (
#             "NetworkError",
#             "Jira API connection failed",
#             f"Internet ya Jira status check karo. Detail: {str(error)[:150]}",
#         )
#     elif any(k in err_str for k in ("groq", "llm", "rate", "quota")):
#         return (
#             "LLMError",
#             "AI model error",
#             f"Groq API key check karo ya baad mein try karo. Detail: {str(error)[:150]}",
#         )
#     else:
#         return (
#             "SystemError",
#             "Jira ticket creation failed",
#             f"Unexpected error: {str(error)[:200]}",
#         )


# async def create_jira_issue_node(state: AgentState) -> dict:
#     """Slack message → Jira ticket → Slack rich card."""
#     event   = state["event"]
#     actions = list(state.get("actions_taken", []))
#     errors  = list(state.get("errors", []))

#     jira  = JiraTool()
#     slack = SlackTool()

#     reply_channel = event.slack_channel or settings.default_slack_channel
#     raw_user_id   = event.slack_user    or "unknown"
#     slack_text    = event.slack_text    or ""

#     if not slack_text.strip():
#         errors.append("empty_slack_message")
#         return {"actions_taken": actions, "errors": errors, "next_action": "finalize"}

#     # Step 1: Slack User ID → Real name
#     reporter = await _get_slack_display_name(raw_user_id)

#     # Step 2: LLM se parse karo
#     issue_payload: JiraIssuePayload | None = None

#     try:
#         logger.info(f"[Jira Creator] Parsing: '{slack_text[:60]}'")

#         llm = ChatGroq(
#             api_key     = settings.groq_api_key,
#             model       = settings.groq_model,
#             temperature = 0.1,
#             max_tokens  = 1024,
#         )
#         llm_response = await llm.ainvoke([
#             SystemMessage(content=SYSTEM_PROMPT),
#             HumanMessage(content=f"Slack message from @{reporter}:\n\n{slack_text}"),
#         ])

#         raw_content  = llm_response.content if isinstance(llm_response.content, str) else str(llm_response.content)
#         clean        = _clean_json(raw_content)
#         data         = json.loads(clean)
#         issue_payload = JiraIssuePayload(**data)

#         logger.info(f"[Jira Creator] Parsed | type={issue_payload.issue_type} | priority={issue_payload.priority}")

#     except Exception as e:
#         etype, short_msg, detail = _classify_error(e)
#         logger.error(f"[Jira Creator] LLM failed: {e}")
#         errors.append(f"llm_parse_failed: {str(e)[:100]}")
#         try:
#             await slack.send_error_alert(channel=reply_channel, error_type=etype,
#                                          short_msg=short_msg, detail=detail,
#                                          source="Jira Creator — LLM Step")
#         except Exception:
#             pass
#         return {"actions_taken": actions, "errors": errors, "next_action": "finalize"}

#     # Step 3: Jira mein create karo
#     jira_result: dict | None = None

#     try:
#         logger.info(f"[Jira Creator] Creating: {issue_payload.summary}")
#         jira_result = await jira.create_issue(issue_payload)
#         actions.append(f"jira_issue_created:{jira_result['key']}")
#         tracker.track_jira_created(jira_result["key"], issue_payload.summary)
#         logger.info(f"[Jira Creator] Created {jira_result['key']}")

#     except Exception as e:
#         etype, short_msg, detail = _classify_error(e)
#         logger.error(f"[Jira Creator] Jira API failed: {e}")
#         errors.append(f"jira_api_failed: {str(e)[:100]}")
#         try:
#             await slack.send_error_alert(channel=reply_channel, error_type=etype,
#                                          short_msg=short_msg, detail=detail,
#                                          source="Jira Creator — API Step")
#         except Exception:
#             pass
#         return {"actions_taken": actions, "errors": errors, "next_action": "finalize"}

#     # Step 4: Slack pe rich card bhejo
#     try:
#         await slack.send_jira_created_card(
#             channel     = reply_channel,
#             issue_key   = jira_result["key"],
#             issue_url   = jira_result["url"],
#             summary     = issue_payload.summary,
#             issue_type  = issue_payload.issue_type,
#             priority    = issue_payload.priority,
#             description = issue_payload.description,
#             labels      = issue_payload.labels,
#             reporter    = reporter,
#         )
#         actions.append("slack_jira_card_sent")
#         logger.info(f"[Jira Creator] Card sent to {reply_channel}")

#     except Exception as e:
#         errors.append(f"slack_card_failed: {str(e)[:100]}")
#         logger.error(f"[Jira Creator] Card failed (issue created OK): {e}")
#         try:
#             await slack.send_message(
#                 channel=reply_channel,
#                 text=(
#                     f"Jira ticket created: *{jira_result['key']}*\n"
#                     f"{issue_payload.summary}\n"
#                     f"Priority: {issue_payload.priority} | Type: {issue_payload.issue_type}\n"
#                     f"Link: {jira_result['url']}"
#                 ),
#             )
#             actions.append("slack_fallback_sent")
#         except Exception:
#             pass

#     return {"actions_taken": actions, "errors": errors, "next_action": "finalize"}
"""
=============================================================================
app/agent/nodes/jira_creator_node.py — JIRA ISSUE CREATOR NODE
=============================================================================
PURPOSE:
  Slack message se automatically proper Jira ticket create karo
  aur team ko rich Slack card mein result dikhao.

TRIGGER KEYWORDS:
  "bug: ..."     → Bug issue
  "issue: ..."   → Task issue
  "task: ..."    → Task issue
  "create: ..."  → Task issue
  "ticket: ..."  → Story issue

STEPS:
  1. Slack message LLM ko bhejo → structured JSON extract karo
  2. LLM error → short classified error card Slack pe
  3. Jira mein ticket create karo
  4. Rich confirmation card Slack pe bhejo

ERRORS FIXED:
  - response.content type-safe extraction (str | list both handled)
  - _clean_json strict str input
  - send_error_alert / send_jira_created_card explicit import check
=============================================================================
"""

import json
from typing import TYPE_CHECKING, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from backend.agent.state import AgentState
from backend.agent.tools.jira_tool import JiraTool
from backend.agent.tools.slack_tool import SlackTool
from backend.core.config import settings
from backend.core.logger import get_logger
from backend.models.responses import JiraIssuePayload
from backend.agent.nodes.summarize_node import generate_ai_summary

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

# =============================================================================
# LLM SYSTEM PROMPT
# =============================================================================
SYSTEM_PROMPT = """You are a project manager assistant who creates well-structured Jira tickets.

Extract issue details from the Slack message and return ONLY this JSON:
{
  "summary": "Clear, actionable issue title (max 100 chars, start with verb)",
  "description": "Detailed description: what happened, where, expected vs actual behavior",
  "issue_type": "Bug" or "Task" or "Story",
  "priority": "Highest" or "High" or "Medium" or "Low" or "Lowest",
  "labels": ["frontend", "backend", "database", "auth", "ui", "api"]
}

Priority guide:
  Highest → Production down, security breach, data loss
  High    → Major feature broken, blocking multiple users
  Medium  → Feature not working correctly, workaround exists
  Low     → Minor issue, cosmetic problem
  Lowest  → Enhancement, nice to have

Return ONLY the JSON. No markdown, no explanation, no extra text."""


# =============================================================================
# HELPER: LLM response → clean string
# =============================================================================

def _extract_content(response_content: Any) -> str:
    """
    LangChain response.content str ya list dono ho sakta hai.
    Ye function hamesha clean string return karta hai.

    Error 1 fix: 'None is not subscriptable' aur type mismatch
    """
    if response_content is None:
        return ""

    # Agar list hai (tool_use responses mein hota hai)
    if isinstance(response_content, list):
        # List mein text blocks dhoondhao
        for block in response_content:
            if isinstance(block, dict) and block.get("type") == "text":
                return str(block.get("text", ""))
            if isinstance(block, str):
                return block
        return ""

    # Already string hai
    return str(response_content)


def _clean_json(raw: str) -> str:
    """
    LLM response se pure JSON extract karo.

    Error 2 fix: parameter strictly str leta hai
    _extract_content() se call karo pehle.
    """
    # None ya empty string guard
    if not raw or not raw.strip():
        raise ValueError("Empty response from LLM")

    raw = raw.strip()

    # Markdown code block remove karo
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


# =============================================================================
# HELPER: Error classify karo
# =============================================================================

def _classify_error(error: Exception) -> tuple[str, str, str]:
    """
    Error → (error_type, short_msg, detail)
    Team ko Slack mein clear, short message mile.
    """
    err_str = str(error).lower()

    # JSON / parse errors — isinstance check pehle (more reliable)
    if (
        isinstance(error, (json.JSONDecodeError, ValueError, KeyError))
        or "json" in err_str
        or "parse" in err_str
        or "expecting" in err_str
        or "decode" in err_str
        or "empty response" in err_str
    ):
        return (
            "ParseError",
            "LLM returned invalid response",
            f"AI model ka response parse nahi ho saka. "
            f"Try again ya manually Jira pe ticket banao. "
            f"Detail: {str(error)[:150]}",
        )

    elif "401" in err_str or "403" in err_str or "auth" in err_str:
        return (
            "AuthError",
            "Jira authentication failed",
            f"Jira API token ya email galat hai. "
            f".env file mein JIRA_EMAIL aur JIRA_API_TOKEN check karo. "
            f"Detail: {str(error)[:150]}",
        )

    elif "404" in err_str:
        return (
            "APIError",
            "Jira project not found",
            f"Project key '{settings.jira_project_key}' Jira mein nahi mila. "
            f".env mein JIRA_PROJECT_KEY check karo.",
        )

    elif "timeout" in err_str or "connect" in err_str or "network" in err_str:
        return (
            "NetworkError",
            "Jira API connection failed",
            f"Jira server se connection nahi hua. "
            f"Internet connection ya Jira status page check karo. "
            f"Detail: {str(error)[:150]}",
        )

    elif "groq" in err_str or "llm" in err_str or "rate" in err_str or "quota" in err_str:
        return (
            "LLMError",
            "AI model error",
            f"Groq LLM se response nahi aaya. "
            f"API key check karo ya thodi der baad try karo. "
            f"Detail: {str(error)[:150]}",
        )

    else:
        return (
            "SystemError",
            "Jira ticket creation failed",
            f"Unexpected error occurred. "
            f"Detail: {str(error)[:200]}",
        )


async def _get_slack_display_name(user_id: str, slack_tool: "SlackTool") -> str:
    """
    Slack User ID (U0B4Q6JBZAQ) → Display Name (Inam ur Rehman)
    Slack users.info API se real naam fetch karo.
    Fail ho toh user_id return karo — graceful fallback.
    """
    if not user_id or not user_id.startswith("U"):
        return user_id or "unknown"

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.slack_api_url}/users.info",
                headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
                params={"user": user_id},
            )
            data = resp.json()
            if data.get("ok"):
                user    = data.get("user", {})
                profile = user.get("profile", {})
                # Real name prefer karo, phir display name, phir username
                return (
                    profile.get("real_name")
                    or profile.get("display_name")
                    or user.get("name")
                    or user_id
                )
    except Exception:
        pass

    return user_id


# =============================================================================
# MAIN NODE FUNCTION
# =============================================================================

async def create_jira_issue_node(state: AgentState) -> dict:
    """
    Slack message/GitHub Push -> Jira ticket -> Slack rich confirmation.
    """
    event   = state["event"]
    actions = list(state.get("actions_taken", []))
    errors  = list(state.get("errors", []))

    jira  = JiraTool()
    slack = SlackTool()

    # FIX: Har haal mein reply_channel select hoga (Default ya Slack se)
    reply_channel = getattr(event, "slack_channel", None) or settings.default_slack_channel
    raw_user_id   = event.slack_user or "unknown"
    reporter      = await _get_slack_display_name(raw_user_id, slack)

    # --- Source text extraction ---
    source_text = ""
    if event.slack_text:
        source_text = event.slack_text
    elif hasattr(event, "github_push") and event.github_push:
        source_text = event.github_push.get("head_commit", {}).get("message", "No commit message")
    
    if not source_text or not source_text.strip():
        source_text = "Automated system update: GitHub push event received."

    # ==========================================================================
    # STEP 1: LLM se message parse karwao
    # ==========================================================================
    issue_payload: JiraIssuePayload | None = None
    ai_summary = "No summary generated."
    
    try:
        logger.info(f"[Jira Creator] Parsing: '{source_text[:60]}'")
        user_prompt = (
            f"Context: {'Slack message' if event.slack_text else 'GitHub Push Event'}\n"
            f"Content:\n{source_text}"
        )   

        llm = ChatGroq(
            api_key     = settings.groq_api_key,
            model       = settings.groq_model,
            temperature = 0.1,
            max_tokens  = 1024,
        )

        llm_response = await llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])

        raw_content = _extract_content(llm_response.content)
        clean       = _clean_json(raw_content)
        data        = json.loads(clean)
        issue_payload = JiraIssuePayload(**data)

        ai_summary = await generate_ai_summary(
            f"Title: {issue_payload.summary}. Description: {issue_payload.description}", 
            context="Jira Ticket"
        )
    except Exception as e:
        error_type, short_msg, detail = _classify_error(e)
        logger.error(f"[Jira Creator] LLM parse failed: {e}")
        errors.append(f"llm_parse_failed: {str(e)[:100]}")
        
        try:
            await slack.send_error_alert(
                channel=reply_channel, error_type=error_type, 
                short_msg=short_msg, detail=detail, source="Jira Creator — LLM Step"
            )
        except Exception as slack_err:
            logger.error(f"[Jira Creator] Slack error alert failed: {slack_err}")
            
        return {"actions_taken": actions, "errors": errors, "next_action": "finalize"}

    # ==========================================================================
    # STEP 2: Jira mein issue create karo
    # ==========================================================================
    jira_result: dict | None = None
    try:
        logger.info(f"[Jira Creator] Creating: {issue_payload.summary}")
        jira_result = await jira.create_issue(issue_payload)

        from backend.main import ws_manager
        await ws_manager.broadcast({
            "type": "jira_ticket",
            "key": jira_result['key'],
            "summary": ai_summary,
            "title": issue_payload.summary,
            "priority": issue_payload.priority,
            "message": f"🎫 Jira Ticket Created: <b>{jira_result['key']}</b>"
        })
        
        actions.append(f"jira_issue_created:{jira_result['key']}")
    except Exception as e:
        error_type, short_msg, detail = _classify_error(e)
        logger.error(f"[Jira Creator] Jira API failed: {e}")
        errors.append(f"jira_api_failed: {str(e)[:100]}")
        try:
            await slack.send_error_alert(
                channel=reply_channel, error_type=error_type, 
                short_msg=short_msg, detail=detail, source="Jira Creator — Jira API Step"
            )
        except Exception as slack_err:
            logger.error(f"[Jira Creator] Slack error alert failed: {slack_err}")
        return {"actions_taken": actions, "errors": errors, "next_action": "finalize"}

    # ==========================================================================
    # STEP 3: Slack pe rich confirmation card bhejo (FIX: Ab GitHub pr bhi chaly ga)
    # ==========================================================================
    if reply_channel:
        try:
            await slack.send_jira_created_card(
                channel     = reply_channel,
                issue_key   = jira_result["key"],
                issue_url   = jira_result["url"],
                summary     = issue_payload.summary,
                issue_type  = issue_payload.issue_type,
                priority    = issue_payload.priority,
                description = issue_payload.description,
                labels      = issue_payload.labels,
                reporter    = reporter,
            )
            actions.append("slack_jira_card_sent")
        except Exception as e:
            errors.append(f"slack_card_failed: {str(e)[:100]}")
            try:
                await slack.send_message(
                    channel=reply_channel,
                    text=f"✅ Jira ticket created: *{jira_result['key']}*\n🔗 {jira_result['url']}"
                )
            except Exception:
                pass

    return {
        "analysis_summary": ai_summary,
        "actions_taken": actions,
        "errors":        errors,
        "next_action":   "finalize",
    }