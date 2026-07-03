# """
# =============================================================================
# backend/agent/nodes/summarize_node.py — COMMIT SUMMARIZATION NODE
# =============================================================================
# """

# from backend.agent.state import AgentState
# from backend.core.llm import get_llm
# from backend.core.logger import get_logger
# from backend.models.events import EventType # Import Enum

# logger = get_logger(__name__)

# async def summarize_push_node(state: AgentState) -> dict:
#     event = state.get("event")
    
#     # DEBUG LOGS: Terminal mein check karein kya event type aa raha hai
#     logger.info(f"DEBUG: Event object received: {event}")
#     logger.info(f"DEBUG: Event type value: {event.event_type}")

#     # Agar event_type Enum hai toh .value use karein, agar string hai toh direct match
#     is_push = (event.event_type == "GITHUB_PUSH" or event.event_type == EventType.GITHUB_PUSH)
    
#     if not is_push:
#         return {"analysis_summary": "No summary needed for this event type."}
    
#     commit_msg = event.commit_msg or "No commit message provided."
#     logger.info(f"Summarizing commit message: {commit_msg}")
    
#     # Prompt refine kiya
#     prompt = f"""
#     You are a professional DevOps Assistant. Summarize this git commit message.
#     Provide a clear, non-technical explanation that explains:
#     1. What was changed.
#     2. Why it is important for the project.
#     Keep it between 15 to 30 words. Make it professional yet easy to understand.
    
#     Commit Message: "{commit_msg}"
#     Summary:
#     """
    
#     try:
#         llm = get_llm()
#         response = await llm.ainvoke(prompt)
#         summary = response.content.strip()
        
#         # Summary ka clean-up (agar quotes mein aaye toh)
#         summary = summary.replace('"', '').strip()
        
#         logger.info(f"Successfully Generated Summary: {summary}")
#         return {"analysis_summary": summary}
        
#     except Exception as e:
#         logger.error(f"Error generating summary via LLM: {e}")
#         return {"analysis_summary": "Summary could not be generated."}


"""
=============================================================================
backend/agent/nodes/summarize_node.py — UNIVERSAL SUMMARIZATION NODE
=============================================================================
PURPOSE:
  Har GitHub event (Push, PR, Issue) ke liye AI summary generate karta hai.
=============================================================================
"""

from backend.agent.state import AgentState
from backend.core.llm import get_llm
from backend.core.logger import get_logger
from backend.models.events import EventType

logger = get_logger(__name__)

async def generate_ai_summary(text: str, context: str = "general event") -> str:
    """Helper function to generate professional summaries for any event."""
    try:
        llm = get_llm()
        prompt = f"""
        You are a professional DevOps Assistant. Summarize the following {context}:
        
        Text: "{text}"
        
        Provide a clear, non-technical explanation that explains:
        1. What was changed/happened.
        2. Why it is important for the project.
        Keep it between 15 to 30 words. Make it professional yet easy to understand.
        Summary:
        """
        response = await llm.ainvoke(prompt)
        summary = response.content.strip().replace('"', '')
        return summary
    except Exception as e:
        logger.error(f"Error generating AI summary: {e}")
        return "Summary could not be generated."

async def summarize_push_node(state: AgentState) -> dict:
    """Node function specifically for Push events in the Graph."""
    event = state.get("event")
    
    # Check if this is a push event
    is_push = (event.event_type == "GITHUB_PUSH" or event.event_type == EventType.GITHUB_PUSH)
    
    if not is_push:
        return {"analysis_summary": "No summary needed for this event type."}
    
    commit_msg = event.commit_msg or "No commit message provided."
    logger.info(f"Summarizing push: {commit_msg}")
    
    # Call the helper
    summary = await generate_ai_summary(commit_msg, context="git commit")
    
    logger.info(f"Generated Push Summary: {summary}")
    return {"analysis_summary": summary}