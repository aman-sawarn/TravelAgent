
import os
import asyncio
import json
from typing import TypedDict, List, Optional

from app.services.flight_service import Search
from app.core.schemas import FetchedFlightSearchDetails

from dotenv import load_dotenv
from langchain.chat_models import ChatHuggingFace
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
# LangGraph / LangChain core imports
from langgraph.graph import StateGraph, START, END

load_dotenv()

# --------------------
# State schema
# --------------------

class TravelState(TypedDict):
    user_query: str
    response: Optional[str]
    action: Optional[str] # name of tool to call, or 'none'
    action_input: Optional[dict]
    results: Optional[List[dict]] # results returned by tools
    itinerary: Optional[dict]

# --------------------
# Utility / mock tools
# --------------------
@tool
def flight_search(origin: str, dest: str, depart_date: str, return_date: Optional[str] = None, passengers: int = 1):
    """
    Search for flights using Amadeus API via the Search service.
    Returns a list of flight offers or an error message.
    """
    try:
        # Construct the search details object
        # Note: Mapping tool args to the schema.
        details = FetchedFlightSearchDetails(
            origin_iata=origin,
            destination_iata=dest,
            departure_date=depart_date,
            return_date=return_date,
            adults=passengers,
            # Default values for fields not exposed to the tool yet
            children=0,
            infants=0,
            currency="INR",
            travel_class="ECONOMY",
            non_stop=False,
            max_results=5
        )
        
        search_service = Search()
        # Execute async search synchronously
        results = asyncio.run(search_service.search_flights_on_a_date(details))
        return results
    except Exception as e:
        return {"error": f"Flight search failed: {str(e)}"}


@tool
def hotel_search(city: str, checkin: str, checkout: str, guests: int = 1):
    """Mock hotel search tool. Replace with calls to Booking/Hotels API."""
    return [
    {"hotel": "The Sample Residency", "price_per_night": "₹4,500", "rating": 4.3},
    {"hotel": "Demo Inn", "price_per_night": "₹3,200", "rating": 3.9},
    ]

if os.getenv("OPENAI_KEY") and not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_KEY")
# Initialize LLM (OpenAI via langchain-openai)
# --------------------
# Make sure OPENAI_API_KEY is set in env
if "OPENAI_API_KEY" not in os.environ:
    raise EnvironmentError("Please set OPENAI_API_KEY in your environment")


# Use init_chat_model to create an LLM instance compatible with LangGraph
# llm = init_chat_model(
#         "openai:gpt-3.5-turbo", # or another OpenAI model string supported by your langchain-openai version
#         temperature=0.2,
#         )
llm = ChatHuggingFace(
    model_name="mosaicml/mpt-7b-instruct",  # HuggingFace model
    model_kwargs={
        "temperature": 0.2,
        "max_new_tokens": 512,
    })
# system prompt to instruct the model how to respond and when to call tools
SYSTEM_PROMPT = SystemMessage(content=(
    """You are TravelAgentGPT. When a user asks for travel help you may either:
    1) answer directly, or
    2) call a tool by returning a JSON object like: {\"action\": \"flight_search\", \"action_input\": { ... }}\n
    If you return a tool call, DO NOT provide the final user-facing answer yet — the graph will run the tool and then ask you again to finalize the response using the tool's results.""")
    )


# --------------------
# Node definitions
# --------------------

# def llm_node(state: TravelState) -> TravelState:
#     """LLM node: decides whether to answer or call a tool.
#     Expects state['user_query'] to contain the user's question and may use state['results'] if present.
#     Returns updated state with either action='none' and response filled, or action set to tool name.
#     """
#     messages = [SYSTEM_PROMPT]


#     # if we have tool results, include them as context to the LLM
#     if state.get("results"):
#         messages.append(HumanMessage(content=f"Tool results: {state['results']}"))


#     messages.append(HumanMessage(content=state["user_query"]))


#     # call the model
#     llm_response = llm.invoke({"messages": messages})


#     # Extract the assistant content. The exact structure returned by llm.invoke depends on your langchain/langgraph versions.
#     # We'll try to find textual content in the returned structure.
#     assistant_messages = llm_response.get("messages") or llm_response.get("output") or []
#     text = None
#     if assistant_messages:
#         # assistant_messages is typically a list of message objects; take the last
#         last = assistant_messages[-1]
#     text = getattr(last, "content", None) or last.get("content") if isinstance(last, dict) else str(last)


#     if text is None:
#         state["response"] = "(model returned no text)"
#         state["action"] = "none"
#         return state


#     # Simple heuristic: if model starts with a JSON-looking tool call, parse it.
#     text_strip = text.strip()
#     if text_strip.startswith("{") and "action" in text_strip:
#         try:
#             import json
#             j = json.loads(text_strip)
#             state["action"] = j.get("action")
#             state["action_input"] = j.get("action_input")
#             state["response"] = None
#             return state
#         except Exception:
#         # fallthrough to answer directly
#             pass


#     # otherwise treat as direct answer
#     state["response"] = text
#     state["action"] = "none"
#     return state

def llm_node(state: TravelState) -> TravelState:
    messages = [SYSTEM_PROMPT]
    if state.get("results"):
        messages.append(HumanMessage(content=f"Tool results: {state['results']}"))
    messages.append(HumanMessage(content=state["user_query"]))

    # Correct call to LLM
    llm_response = llm(messages)  # pass the list of messages directly

    # Extract text
    text = llm_response.content if hasattr(llm_response, "content") else str(llm_response)

    # Handle tool call vs direct answer
    text_strip = text.strip()
    if text_strip.startswith("{") and "action" in text_strip:
        try:
            j = json.loads(text_strip)
            state["action"] = j.get("action")
            state["action_input"] = j.get("action_input")
            state["response"] = None
            return state
        except Exception:
            pass

    state["response"] = text
    state["action"] = "none"
    return state


def flight_tool_node(state: TravelState) -> TravelState:
    """Calls the flight_search tool when requested. Expects action_input to contain origin/dest/dates."""
    ai = state.get("action_input") or {}
    origin = ai.get("origin")
    dest = ai.get("dest")
    depart = ai.get("depart_date")
    ret = ai.get("return_date")
    passengers = ai.get("passengers", 1)


    results = flight_search(origin, dest, depart, return_date=ret, passengers=passengers)
    state["results"] = results
    # clear action so the graph will route back to the LLM for a final answer
    state["action"] = "none"
    return state




def hotel_tool_node(state: TravelState) -> TravelState:
    ai = state.get("action_input") or {}
    city = ai.get("city")
    checkin = ai.get("checkin")
    checkout = ai.get("checkout")
    guests = ai.get("guests", 1)


    results = hotel_search(city, checkin, checkout, guests)
    state["results"] = results
    state["action"] = "none"
    return state


# --------------------
# Build the StateGraph
# --------------------


# Create the graph builder using our state schema
graph_builder = StateGraph(TravelState)

# Add nodes
graph_builder.add_node("llm", llm_node)
graph_builder.add_node("flight_tool", flight_tool_node)
graph_builder.add_node("hotel_tool", hotel_tool_node)


# Wire edges: start -> llm
graph_builder.add_edge(START, "llm")


# After llm: conditional edge -> if it produced a tool call route to that tool, otherwise END
# We use a small helper to inspect the state's 'action' value at runtime.

def llm_should_call_tool(state: TravelState) -> str:
    """Return key 'call_tool' or 'end' depending on state"""
    if state.get("action") and state["action"] != "none":
        return "call_tool"
    return "end"


# Add conditional edge mapping. When llm_node runs, llm_should_call_tool decides which branch to take.
graph_builder.add_conditional_edges("llm", llm_should_call_tool,
    {
    "end": END,
    "call_tool": "flight_tool" # we'll route all tool calls to flight_tool/hotel_tool via a small router node; simpler option: use separate conditions
    }
    )

## NOTE: For a production-grade graph you'd create a router node that looks at state['action'] and dispatches to the correct tool node.
# For clarity here we add a tiny router node:


def tool_router_node(state: TravelState) -> TravelState:
    a = state.get("action")
    if a == "flight_search":
        return flight_tool_node(state)
    elif a == "hotel_search":
        return hotel_tool_node(state)
    else:
    # unknown tool -> no-op
        state["results"] = [{"error": "unknown tool or missing action_input"}]
    return state

graph_builder.add_node("tool_router", tool_router_node)
# adjust edges: when call_tool selected, go to tool_router and then back to llm
graph_builder.add_edge("llm", "tool_router")
graph_builder.add_edge("tool_router", "llm")


# end -> finish
graph_builder.add_edge("llm", END)


# Compile the graph into a runnable app
app = graph_builder.compile(name="travel_agent_app")

# --------------------
# Run example
# --------------------
if __name__ == "__main__":
    # example user query asking to find flights
    init_state: TravelState = {
    "user_query": (
    "I want to fly from Bangalore to Goa on 2025-11-10. Find cheapest flights for 1 passenger."
    ),
    "response": None,
    "action": None,
    "action_input": None,
    "results": None,
    "itinerary": None,
    }


    # invoke the graph. The exact invocation signature may vary across versions; many examples use app.invoke({"messages": [...]})
    output = app.invoke(init_state)


    # The compiled graph returns the final state. Print it.
    print("Final state:")
    print(output)


    # If the graph left a user-facing response, show it
    if output.get("response"):
        print("\nAssistant:\n", output["response"])