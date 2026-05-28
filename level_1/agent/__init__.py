"""
Level 1: Mission Analysis AI - Multi-Agent System

This package contains the multi-agent system for crash site analysis:
- Root orchestrator (MissionAnalysisAI) with before_agent_callback
- Parallel analysis crew (EvidenceAnalysisCrew)
- Specialist agents (Geological, Botanical, Astronomical)

Key ADK Patterns Used:
1. before_agent_callback: Fetches participant config and sets state
2. {key} State Templating: Sub-agents access state via {soil_url}, etc.
3. ToolContext: Tools access state via tool_context.state.get()
4. ParallelAgent: Runs specialists concurrently
"""

def __getattr__(name: str):
    if name == "root_agent":
        from agent.agent import root_agent
        return root_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["root_agent"]