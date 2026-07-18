"""
Root Agent
Google ADK root agent that delegates to specialized sub-agents.
"""
from google.adk.agents import Agent

from adk_app.agents.loan_qualification_agent import loan_qualification_agent
from adk_app.agents.philippines_voice_agent import philippines_voice_agent
from adk_app.agents.indonesia_voice_agent import indonesia_voice_agent
from adk_app.agents.realtime_nudge_agent import realtime_nudge_agent


ROOT_AGENT_INSTRUCTION = """You are the root orchestration agent for the QuickFund AI Voice Assessment system. You delegate conversations to the appropriate specialized agent based on the context.

## Available Sub-Agents

1. **loan_qualification_agent**: Handles small business loan qualification conversations in English. Use this for Q1 assessment demos.
2. **philippines_voice_agent**: Handles Philippine bancassurance/insurance renewal conversations in English, Filipino, and Taglish. Use this for Q3 Philippines demos.
3. **indonesia_voice_agent**: Handles Indonesian consumer finance installment reminders in formal/colloquial Bahasa Indonesia. Use this for Q3 Indonesia demos.
4. **realtime_nudge_agent**: Analyzes transcript chunks for real-time nudges. Use this for Q4 assessment demos.

## Routing Logic

- If the conversation is about **business loans, loan qualification, or lending products** → delegate to `loan_qualification_agent`
- If the conversation involves **Filipino/Tagalog, Philippine insurance, or bancassurance** → delegate to `philippines_voice_agent`
- If the conversation involves **Bahasa Indonesia, Indonesian finance, or cicilan/installment** → delegate to `indonesia_voice_agent`
- If the input is a **transcript chunk for analysis** (typically marked with metadata) → delegate to `realtime_nudge_agent`
- For **general questions** about the assessment system, answer directly.

## Default

If unsure which agent to use, default to the loan qualification agent.
"""

root_agent = Agent(
    name="root_agent",
    model="gemini-2.0-flash",
    description="Root orchestration agent that delegates to specialized sub-agents for loan qualification, Philippines/Indonesia localized bots, and real-time nudge analysis.",
    instruction=ROOT_AGENT_INSTRUCTION,
    sub_agents=[
        loan_qualification_agent,
        philippines_voice_agent,
        indonesia_voice_agent,
        realtime_nudge_agent,
    ],
)
