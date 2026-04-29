# Import and Setup
# Install (if needed)
# pip install langgraph langchain langchain-openai neo4j

from typing import TypedDict, Literal, Optional, Dict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_community.graphs import Neo4jGraph

import os

# API key setup
os.environ["OPENAI_API_KEY"] = ""

# Initialize LLM
llm = ChatOpenAI(model="gpt-5.4-nano", temperature=0)

# Initialize Neo4j connection
graph = Neo4jGraph(
    url="neo4j://localhost:7687",
    username="neo4j",
    password="chatwithgermany"
)

# =========================
# STATE DEFINITION
# =========================
class AgentState(TypedDict):
    # INPUT
    question: str  

    # INTERPRETATION
    intent: str  
    entity_name: str  

    # ENTITY RESOLUTION
    source_type: str  
    target_type: str  

    # HIERARCHY
    direction: str   # "up" | "down" | "same"

    # 🌍 SPATIAL (NEW)
    cardinal_direction: Optional[str]   # e.g. "northern", "southern", etc.

    distance_filter: Optional[Dict]    
    # {
    #   "operator": "<", ">", "<=", ">=", "="
    #   "value": 10,
    #   "unit": "km"
    # }

    # QUERY
    cypher_query: str  

    # OUTPUT
    result: str  

# =========================
# HIERARCHY DEFINITION
# =========================
HIERARCHY = [
    "City",
    "District",
    "AdministrativeDistrict",
    "FederalState"
]

# =========================
# NORMALIZER
# Maps free text to graph labels
# =========================
def normalize(text: str):
    text = text.lower()

    mapping = {
        "city": "City",
        "stadt": "City",
        "städte": "City",

        "administrative District": "AdministrativeDistrict",
        "administrative": "AdministrativeDistrict",
        "Verwaltungsbezirk": "AdministrativeDistrict",

        "district": "District",
        "kreis": "District",
        "landkreis": "District",

        "bundesland": "FederalState",
        "bundesländer": "FederalState",
        "state": "FederalState",
        "federal": "FederalState",
    }

    for k, v in mapping.items():
        if k in text:
            return v

    return None

# =========================
# SAFE JSON PARSER
# Ensures valid structure from LLM output
# =========================
def safe_parse(response: str):
    import json

    try:
        data = json.loads(response)
    except Exception:
        # full fallback if parsing fails
        return {
            "intent": "within",
            "entity_name": "",
            "cardinal_direction": None,
            "distance_filter": None
        }

    # required fields
    data.setdefault("intent", "within")
    data.setdefault("entity_name", "")

    # spatial fields
    data.setdefault("cardinal_direction", None)
    data.setdefault("distance_filter", None)

    # validate intent
    if data["intent"] not in ["within", "touches", "relates"]:
        data["intent"] = "within"

    # normalize cardinal direction
    if data.get("cardinal_direction"):
        dir_raw = data["cardinal_direction"].lower()

        mapping = {
            "north": "northern",
            "south": "southern",
            "east": "eastern",
            "west": "western",
            "northeast": "northeastern",
            "northwest": "northwestern",
            "southeast": "southeastern",
            "southwest": "southwestern"
        }

        data["cardinal_direction"] = mapping.get(dir_raw, dir_raw)

    # validate distance filter structure
    if data.get("distance_filter"):
        df = data["distance_filter"]

        if isinstance(df, dict):
            data["distance_filter"] = {
                "operator": df.get("operator"),
                "value": df.get("value"),
                "unit": df.get("unit")
            }

            # if all empty → set None
            if all(v is None for v in data["distance_filter"].values()):
                data["distance_filter"] = None
        else:
            data["distance_filter"] = None

    return data

# =========================
# INTERPRET USER QUERY (LLM)
# =========================
def interpret_query(state):
    prompt = f""" ... """  # (unchanged prompt)

    response = llm.invoke(prompt).content
    parsed = safe_parse(response)

    return {
        **state,
        "intent": parsed.get("intent"),
        "entity_name": parsed.get("entity_name"),
        "cardinal_direction": parsed.get("cardinal_direction"),
        "distance_filter": parsed.get("distance_filter")
    }

# =========================
# RESOLVE SOURCE ENTITY TYPE
# Uses DB first, then LLM if ambiguous
# =========================
def resolve_entity_type(state):
    query = """
    MATCH (n)
    WHERE toLower(n.Name) = toLower($name)
    RETURN labels(n)[0] AS type
    """

    results = graph.query(query, {"name": state["entity_name"]})

    types = list(set(r["type"] for r in results))

    # case 1: single type → done
    if len(types) == 1:
        return {**state, "source_type": types[0]}
    
    # fallback if nothing found
    if not results:
        return {**state, "source_type": "District"}

    # case 2: ambiguous → use LLM
    prompt = f""" ... """  # unchanged

    response = llm.invoke(prompt).content
    parsed = safe_parse(response)

    source_type = parsed.get("source_type")

    # fallback safety
    if source_type not in types:
        source_type = types[0]

    return {
        **state,
        "source_type": source_type
    }

# =========================
# RESOLVE TARGET TYPE
# =========================
def resolve_target_type(state):
    
    intent = state["intent"]
    question = state["question"]
    source_type = state["source_type"]

    # fast path for touches (same level)
    if intent == "touches":
        return {**state, "target_type": source_type}

    # otherwise LLM
    prompt = f""" ... """

    response = llm.invoke(prompt).content
    parsed = safe_parse(response)

    target_type = parsed.get("target_type")

    VALID = ["City", "District", "AdministrativeDistrict", "FederalState"]

    if target_type not in VALID:
        target_type = source_type

    return {
        **state,
        "target_type": target_type
    }

# =========================
# DIRECTION INFERENCE
# =========================
def infer_direction(source, target):
    if source not in HIERARCHY or target not in HIERARCHY:
        return "down"

    s = HIERARCHY.index(source)
    t = HIERARCHY.index(target)

    if s > t:
        return "down"
    if s < t:
        return "up"
    return "same"

def add_direction(state):
    return {
        **state,
        "direction": infer_direction(
            state["source_type"],
            state["target_type"]
        )
    }

# =========================
# ROUTING
# =========================
def select_query_type(state):
    if state["intent"] == "within":
        return f"within_{state['direction']}"
    return f"{state['intent']}_action"

# =========================
# WITHIN QUERIES
# =========================
def build_within_up(state): ...
def build_within_down(state): ...

# =========================
# TOUCHES QUERY
# =========================
def build_touches_query(state): ...

# =========================
# RELATES QUERY (direction + distance)
# =========================
def build_relates_query(state): ...

# =========================
# EXECUTION
# =========================
def execute_query(state):
    result = graph.query(state["cypher_query"])
    cleaned = [r["result"] for r in result]
    return {**state, "result": cleaned}

# =========================
# FINAL VERBALIZATION
# =========================
def verbalize(state):
    prompt = f"""
Turn into natural English:

Question: {state['question']}
Result: {state['result']}
"""
    return {
        **state,
        "result": llm.invoke(prompt).content
    }

# =========================
# GRAPH BUILDING
# =========================
workflow = StateGraph(AgentState)

workflow.add_node("interpret_query", interpret_query)
workflow.add_node("resolve_entity_type", resolve_entity_type)
workflow.add_node("resolve_target_type", resolve_target_type)
workflow.add_node("add_direction", add_direction)

workflow.add_node("build_within_up", build_within_up)
workflow.add_node("build_within_down", build_within_down)
workflow.add_node("build_touches_query", build_touches_query)
workflow.add_node("build_relates_query", build_relates_query)

workflow.add_node("execute_query", execute_query)
workflow.add_node("verbalize", verbalize)

workflow.add_edge(START, "interpret_query")
workflow.add_edge("interpret_query", "resolve_entity_type")
workflow.add_edge("resolve_entity_type", "resolve_target_type")
workflow.add_edge("resolve_target_type", "add_direction")

workflow.add_conditional_edges(
    "add_direction",
    select_query_type,
    {
        "within_up": "build_within_up",
        "within_down": "build_within_down",
        "touches_action": "build_touches_query",
        "relates_action": "build_relates_query"
    }
)

workflow.add_edge("build_within_up", "execute_query")
workflow.add_edge("build_within_down", "execute_query")
workflow.add_edge("build_touches_query", "execute_query")
workflow.add_edge("build_relates_query", "execute_query")

workflow.add_edge("execute_query", "verbalize")
workflow.add_edge("verbalize", END)

compiled_graph = workflow.compile()

# from IPython.display import Image, display
# display(Image(compiled_graph.get_graph().draw_mermaid_png()))

# =========================
# TESTING
# =========================

# print(compiled_graph.invoke({
#     "question": "Which Cities lie in the administrative District of Münster?"
# }))

# print(compiled_graph.invoke({
#     "question": "In which federal State lies Selm?"
# }))
# compiled_graph.invoke({
#     "question": "What Cities lie in Rhein-Sieg-Kreis?"
# })
# print(compiled_graph.invoke({
#     "question": "Which administrative Districts lie next to Düsseldorf?"
# }))

# print(compiled_graph.invoke({
#     "question": "Which City lie in a 10 km distance of Selm?"
# }))
print(compiled_graph.invoke({
    "question": "What is the distance between Bocholt and Siegburg?"
}))