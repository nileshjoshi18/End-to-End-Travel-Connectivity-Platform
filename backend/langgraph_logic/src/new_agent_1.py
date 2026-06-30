"""
new_agent_1.py  —  LangGraph agent for Mumbai Transit AI

Architecture: ThinkAct -> Tools -> Synthesize (2 LLM calls)

CHANGES from previous version:
  - run_sql REMOVED — agent has no direct DB access anymore
  - get_connectivity REMOVED — merged into get_routes (handles both
    single-leg and multi-leg internally)
  - Tools are now DIRECT PYTHON FUNCTION CALLS (routing_results.get_routes,
    train_details.get_train_details) — not HTTP requests to API endpoints.
    The agent and the FastAPI layer both call the same underlying functions.
  - crowd_node REMOVED entirely — get_routes() already returns crowd_scores
    in its response, so there's nothing left to fetch separately.
  - Output shape now matches the old resultant-routes / get_routes format
    exactly, with one added field: ai_summary.

Input: agent now takes (source, destination, user_time) — same shape as
get_routes() — instead of a free-text query.
"""

import os
import json
import asyncio
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from typing import TypedDict, Annotated
import operator

from routing_results import get_routes as _get_routes_impl
from train_details import get_train_details as _get_train_details_impl
from prompts import THINK_ACT_PROMPT, SYNTHESIZE_PROMPT, ACT_FOLLOWUP_PROMPT

load_dotenv()

# ──────────────────────────── LLMs ──────────────────────────────────────

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0,
)

llm_synth = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0,
)

# ─────────────────────── Tools (direct function calls) ──────────────────
# These wrap the actual routing_results / train_details Python functions
# directly — NOT HTTP calls to the API layer. The FastAPI /get_routes and
# /get_train_details endpoints call the SAME underlying functions, so
# agent and API stay perfectly in sync with zero duplication.

@tool
async def get_routes(start_stop: str, end_stop: str, user_time: str) -> str:
    """Get the best route between two Mumbai stations (handles both direct
    same-line trains and multi-leg interchange journeys automatically).
    Pass station NAMES or addresses, e.g. 'Panvel', 'Versova metro station'.
    Returns source/dest stations, departure/arrival, fare, legs, and crowd scores."""
    try:
        result = await _get_routes_impl(start_stop, end_stop, user_time)
        return json.dumps(result, default=str)
    except ValueError as e:
        return f"No route found: {e}"
    except Exception as e:
        return f"Error: {e}"


@tool
async def get_train_details(train_id: str) -> str:
    """Get the full stop-by-stop schedule for a specific train/schedule ID."""
    try:
        result = await asyncio.to_thread(_get_train_details_impl, train_id)
        return json.dumps(result, default=str)
    except Exception as e:
        return f"Error: {e}"


tools_list     = [get_routes, get_train_details]
llm_with_tools = llm.bind_tools(tools_list)
tool_node      = ToolNode(tools_list)

# ──────────────────────────── slim helper ────────────────────────────────

def _slim_tool_result(tool_name: str, raw_content: str) -> str:
    """Strip heavy train_details.stops arrays before passing to synthesize LLM."""
    if tool_name != "get_routes":
        return raw_content
    try:
        data = json.loads(raw_content)
    except (json.JSONDecodeError, TypeError):
        return raw_content

    if "legs" not in data:
        return raw_content

    slim_legs = []
    for leg in data["legs"]:
        slim_legs.append({
            "from_stop": leg.get("from_stop"), "to_stop": leg.get("to_stop"),
            "line": leg.get("line"), "train_id": leg.get("train_id"),
            "departure": leg.get("departure"), "arrival": leg.get("arrival"),
        })

    return json.dumps({
        "start_stop":     data.get("start_stop"),
        "end_stop":        data.get("end_stop"),
        "source_station":  data.get("source_station"),
        "dest_station":    data.get("dest_station"),
        "requested_time":  data.get("requested_time"),
        "final_arrival":   data.get("final_arrival"),
        "legs":            slim_legs,
        "leg_fares":       data.get("leg_fares"),
        "crowd_scores":    data.get("crowd_scores"),
    })


def _full_tool_result(tool_name: str, raw_content: str) -> dict | None:
    """Parse the FULL (non-slimmed) get_routes result — this becomes the
    base of the final /ask response, since output must match get_routes shape."""
    if tool_name != "get_routes":
        return None
    try:
        data = json.loads(raw_content)
        if "legs" in data:
            return data
    except (json.JSONDecodeError, TypeError):
        pass
    return None


class AgentState(TypedDict):
    source:            str
    destination:       str
    user_time:         str
    messages:           Annotated[list, operator.add]
    slim_tool_results:  str
    prior_reasoning:    str
    routing_data:       dict | None   # full get_routes() result, captured from tool call



def think_act_node(state: AgentState) -> AgentState:
    """
    LLM call #1: think + call get_routes for the given source/destination/time.

    IMPORTANT: the SystemMessage and initial HumanMessage are stored into
    state["messages"] (not just passed inline and discarded) so that every
    subsequent node sees the FULL conversation from the start. Gemini
    requires the complete turn history on every call — it has no persistent
    server-side context — and the system instruction must remain the very
    first message in that history on every single invoke().
    """
    user_query = (
        f"Find the route from '{state['source']}' to '{state['destination']}' "
        f"at time '{state['user_time']}'."
    )
    opening_messages = [
        SystemMessage(content=THINK_ACT_PROMPT),
        HumanMessage(content=user_query),
    ]
    response = llm_with_tools.invoke(opening_messages)
    prior = response.content if isinstance(response.content, str) else ""

    # Persist the FULL turn (system + human + AI response) into state,
    # not just the AI response — this is what act_node will build on.
    return {
        "messages": opening_messages + [response],
        "prior_reasoning": prior,
    }


def act_node(state: AgentState) -> AgentState:
    """
    Subsequent act iterations — decide to call one more tool or stop (DONE).

    Gemini requires strict turn ordering: every ToolMessage must immediately
    follow its parent AIMessage(tool_calls=...), and the SystemMessage that
    started the conversation must remain present and first in the list on
    every call (Gemini has no memory between invoke() calls). Since
    think_act_node now persists [System, Human, AI, ...] into state, and
    ToolNode appends ToolMessage(s) after the AI message, state["messages"]
    already has the correct shape — we just invoke on it directly and
    append our followup instruction as a trailing HumanMessage (a valid
    "user turn" immediately after the function-response turn).
    """
    messages = state["messages"] + [HumanMessage(content=ACT_FOLLOWUP_PROMPT)]
    response = llm_with_tools.invoke(messages)
    extra = response.content if isinstance(response.content, str) else ""
    combined = (state.get("prior_reasoning", "") + "\n" + extra).strip() if extra else state.get("prior_reasoning", "")

    # Persist the followup HumanMessage too, so the next act_node call (if any)
    # still sees a complete, correctly-ordered history.
    return {
        "messages": [HumanMessage(content=ACT_FOLLOWUP_PROMPT), response],
        "prior_reasoning": combined,
    }


def collect_node(state: AgentState) -> AgentState:
    """
    Pure Python, zero LLM calls. Slims tool results for the synthesize prompt
    AND captures the full get_routes() payload to use as the response base.
    """
    slim_parts   = []
    routing_data = None

    for msg in state["messages"]:
        if not (hasattr(msg, "name") and msg.name):
            continue
        slimmed = _slim_tool_result(msg.name, msg.content)
        slim_parts.append(f"[{msg.name}]\n{slimmed}")

        full = _full_tool_result(msg.name, msg.content)
        if full is not None:
            routing_data = full  # last successful get_routes call wins

    return {
        "slim_tool_results": "\n\n".join(slim_parts),
        "routing_data":      routing_data,
    }


def synthesize_node(state: AgentState) -> AgentState:
    """
    LLM call #2: generate ONLY the ai_summary text from the routing data.
    The final response is built in run_agent() by taking routing_data as-is
    and attaching this summary — the LLM never touches numeric/structural fields.
    """
    response = llm_synth.invoke([
        SystemMessage(content=SYNTHESIZE_PROMPT),
        HumanMessage(content=(
            f"AI REASONING:\n{state['prior_reasoning'] or '(none)'}\n\n"
            f"ROUTING DATA:\n{state['slim_tool_results'] or 'No tool results.'}\n\n"
            "Produce ONLY the AI SUMMARY paragraph (50-100 words) described in your "
            "instructions. Do not output tables, headers, or anything else — just the summary text."
        )),
    ])
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "collect"


def build_agent():
    g = StateGraph(AgentState)
    g.add_node("think_act",  think_act_node)
    g.add_node("act",        act_node)
    g.add_node("tools",      tool_node)
    g.add_node("collect",    collect_node)
    g.add_node("synthesize", synthesize_node)

    g.set_entry_point("think_act")
    g.add_conditional_edges("think_act", should_continue, {"tools": "tools", "collect": "collect"})
    g.add_edge("tools", "act")
    g.add_conditional_edges("act", should_continue, {"tools": "tools", "collect": "collect"})
    g.add_edge("collect",    "synthesize")
    g.add_edge("synthesize", END)
    return g.compile()


agent = build_agent()


async def run_agent(source: str, destination: str, user_time: str) -> dict:
    """
    Public entry point for the /ask endpoint.

    Returns a dict in EXACTLY the same shape as get_routes(), plus one
    extra field: "ai_summary".

    If the agent failed to produce routing data (e.g. no route exists),
    raises ValueError so the FastAPI layer can return a clean 404.
    """
    result = await agent.ainvoke({
        "source": source, "destination": destination, "user_time": user_time,
        "messages": [], "slim_tool_results": "", "prior_reasoning": "",
        "routing_data": None,
    })

    routing_data = result.get("routing_data")
    if routing_data is None:
        raise ValueError("Agent could not find a viable route for this query.")

    ai_summary = result["messages"][-1].content.strip()

    # Build final response: routing_data fields as-is + ai_summary appended
    final = dict(routing_data)
    final["ai_summary"] = ai_summary
    return final


if __name__ == "__main__":
    import sys

    args = sys.argv[1:]
    source      = args[0] if len(args) > 0 else "Panvel"
    destination = args[1] if len(args) > 1 else "Vashi"
    user_time   = args[2] if len(args) > 2 else "20:00"

    print(f"Query: {source} -> {destination} at {user_time}\n")

    async def debug_run():
        result = await run_agent(source, destination, user_time)
        print(json.dumps(result, indent=2, default=str))

    asyncio.run(debug_run())