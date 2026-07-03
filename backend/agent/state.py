"""
=============================================================================
backend/agent/state.py — LANGGRAPH AGENT STATE
=============================================================================
AgentState = AI agent ki memory ek event ke dauran.
Ek node se doosre node tak ye state flow karti hai.
Har node state padhta hai aur apna result likhta hai.
=============================================================================
"""

from typing import Annotated
from typing_extensions import TypedDict

from backend.models.events import IncomingEvent
from backend.models.responses import OrchestratorResponse, PRAnalysisResult


class AgentState(TypedDict):
    """Agent ki poori memory — ek event ke liye."""
    event:          IncomingEvent
    messages:       Annotated[list, lambda x, y: x + y]  # Append, overwrite nahi
    pr_analysis:    PRAnalysisResult | None
    analysis_summary: str | None  # Naya field: AI generated simple summary
    next_action:    str
    actions_taken:  list[str]
    errors:         list[str]
    final_response: OrchestratorResponse | None