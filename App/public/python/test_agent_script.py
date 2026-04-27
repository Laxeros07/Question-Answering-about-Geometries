# Import und Setup
# Install (falls nötig)
# pip install langgraph langchain langchain-openai neo4j

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_community.graphs import Neo4jGraph

import os
# API
os.environ["OPENAI_API_KEY"] = ""

llm = ChatOpenAI(model="gpt-5.4-nano", temperature=0)

graph = Neo4jGraph(
    url="neo4j://localhost:7687",
    username="neo4j",
    password="chatwithgermany"
)
# State
from typing import TypedDict

class AgentState(TypedDict):
    # INPUT
    question: str  
    # User Question 

    # INTERPRETATION (durch LLM)
    intent: str  
    # Question Type:
    # - "within"  → Hierachy
    # - "touches" → Neighbourhood
    # - "relates"
    # → is used for routing in the grap
    
    entity_name: str  
    # Name of the entity

    source_type: str  
    # Starting Node in the Graph
    # Example: "City", "District", "AdministrativeDistrict", "FederalState"

    target_type: str  
    # End Node in the Graph
    # Important for:
    # - Direction
    # - Step Count

    direction: str  
    # - "up" District → FederalState)
    # - "down" FederalState → District)
    # → decides, which Query-Logic is used

    # QUERY GENERATION
    cypher_query: str  
    # Neo4j Cypher Query

    # OUTPUT
    result: str  
# Hierarchy
HIERARCHY = [
    "City",
    "District",
    "AdministrativeDistrict",
    "FederalState"
]
# Normalizer
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
# Parsing
def safe_parse(response):
    import json
    try:
        data = json.loads(response)
    except:
        return {"intent": "within", "entity_name": ""}

    data.setdefault("intent", "within")
    data.setdefault("entity_name", "")

    return data
# Interpret Query
def interpret_query(state):
    prompt = f"""
Classify the question into one of these intents:

- "within": hierarchical containment (lies in, belongs to, is in)
- "touches": geographic neighbors (lies next to, is next to, touches)
- "relates": generic relation

Find out the entity name. The The entity name is the name of a place in Germany.

Question:
{state['question']}

Return JSON:
{{
  "intent": "...",
  "entity_name": "..."
}}

Rules:
- "lies in", "in which ..." → ALWAYS "within"
- "Which ... lie in ..." → ALWAYS "within"
- "next to" → ALWAYS "touches"
- "relates" → ALWAYS "relates"

-The entity name is never a word like: 
- "City", "Cities",
- "District", "Districts"
- "Administrative", "federal", "State"
"""

    response = llm.invoke(prompt).content
    parsed = safe_parse(response)

    return {
        **state,
        "intent": parsed["intent"],
        "entity_name": parsed["entity_name"]
    }


# Entity Type Resolver
def resolve_entity_type(state):
    
    query = """
    MATCH (n)
    WHERE toLower(n.Name) = toLower($name)
    RETURN labels(n)[0] AS type
    """

    results = graph.query(query, {"name": state["entity_name"]})

    types = list(set(r["type"] for r in results))
    # ✅ FALL 1: one result
    if len(types) == 1:
        return {**state, "source_type": types[0]}
    
    if not results:
        return {**state, "source_type": "District"}  # or None if you prefer strictness

    # ✅ FALL 2: several results → LLM
    prompt = f"""
You are resolving entity ambiguity in a geographic database.

Question:
{state["question"]}

Entity:
{state["entity_name"]}

Possible types:
{types}

Hierarchy:
City < District < AdministrativeDistrict < FederalState

Task:
Pick the MOST appropriate type for the entity in this question.

Rules:
- If a Type ("City | District | AdministrativeDistrict | FederalState") is stated in the question like in the following examples:
    - If "administrative District of" or "the administrative District ..." is in the question → the source type = AdministrativeDistrict
    - If "District of" or "the District ..." is in the question → the source type = District
    - If "federal State of" or "the federal State ..." is in the question → the source type = FederalState
use them as source type in every case

- If asking "Which Cities lie within ..." → the source type must be: "District" or "AdministrativeDistrict" or "FederalState"
- If asking "Which Districts lie within ..." → the source type must be: "AdministrativeDistrict" or "FederalState"
- If asking "Which administrative Districts lie within ..." → the source type must be: "FederalState"
- If asking "liegt in Bundesland" → entity is usually a City
- If "touches" → same level entities

Return ONLY JSON:
{{
  "source_type": "City | District | AdministrativeDistrict | FederalState"
}}
"""

    response = llm.invoke(prompt).content

    parsed = safe_parse(response)

    source_type = parsed.get("source_type")

    # fallback falls LLM Müll liefert
    if source_type not in types:
        source_type = types[0]

    return {
        **state,
        "source_type": source_type
    }
# Target Type
def resolve_target_type(state):
    
    intent = state["intent"]
    question = state["question"]
    source_type = state["source_type"]

    # ✅ FAST PATH (no LLM needed)
    if intent == "touches":
        return {**state, "target_type": source_type}

    # ✅ LLM for everything else
    prompt = f"""
You are determining the TARGET entity type in a geographic query.

Question:
{question}

Source entity type:
{source_type}

Hierarchy:
City < District < AdministrativeDistrict < FederalState

Intent:
{intent}

Task:
Determine what type of entities the user is asking for.

Rules:
- "In which administrative District lies ... → target type = AdministrativeDistrict
- "In which District lies ... → target type = District
- "In which federal State lies ... → target type = FederalState

- "Which Cities lie in ..." → target type = City
- "Which administrative Districts lie in ..." → target type = AdministrativeDistrict
- "Which Districts lie in ..." → target type = District

- "touches" → same type as source
- If unclear → choose the most logical level based on hierarchy

Return ONLY JSON:
{{
  "target_type": "City | District | AdministrativeDistrict | FederalState"
}}
"""

    response = llm.invoke(prompt).content
    parsed = safe_parse(response)

    target_type = parsed.get("target_type")

    # ✅ fallback safety
    VALID = ["City", "District", "AdministrativeDistrict", "FederalState"]

    if target_type not in VALID:
        # smart fallback based on direction intuition
        target_type = source_type

    return {
        **state,
        "target_type": target_type
    }

# Direction
def infer_direction(source, target):
    if source not in HIERARCHY or target not in HIERARCHY:
        return "down"  # safe fallback

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

# Routing
def select_query_type(state):
    if state["intent"] == "within":
        return f"within_{state['direction']}"

    return f"{state['intent']}_action"

# Within
def build_within_up(state):
    source = state["source_type"]
    target = state["target_type"]
    name = state["entity_name"]

    start = HIERARCHY.index(source)
    end = HIERARCHY.index(target)

    query = f"MATCH (start:{source} {{Name: '{name}'}})"

    current = "start"

    for i in range(start, end):
        next_level = HIERARCHY[i + 1]

        next_var = f"n{i}"

        query += f"""
        MATCH ({current})
        -[:hasFootprint]->(:Geometry)
        -[:within]->(:Geometry)
        <-[:hasFootprint]-({next_var}:{next_level})
        """

        current = next_var

    query += f"\nRETURN {current}.Name AS result"

    return {**state, "cypher_query": query}

def build_within_down(state):
    source = state["source_type"]
    target = state["target_type"]
    name = state["entity_name"]

    start = HIERARCHY.index(source)
    end = HIERARCHY.index(target)

    query = f"MATCH (start:{source} {{Name: '{name}'}})"

    current = "start"

    for i in range(start, end, -1):
        lower = HIERARCHY[i - 1]

        next_var = f"n{i}"

        query += f"""
        MATCH ({current})
        -[:hasFootprint]->(:Geometry)
        <-[:within]-(:Geometry)
        <-[:hasFootprint]-({next_var}:{lower})
        """

        current = next_var

    query += f"\nRETURN {current}.Name AS result"

    return {**state, "cypher_query": query}
# touches
def build_touches_query(state):
    return {
        **state,
        "cypher_query": f"""
        MATCH p=
        (:{state['source_type']} {{Name: '{state['entity_name']}'}})
        -[:hasFootprint]->(:Geometry)
        <-[:touches]-(:Geometry)
        <-[:hasFootprint]-(:{state['source_type']})
        RETURN p
        """
    }
# relates
def build_relates_query(state):
    return {
        **state,
        "cypher_query": f"""
        MATCH p=
        (:{state['source_type']} {{Name: '{state['entity_name']}'}})
        -[:relates]->(:{state['source_type']})
        RETURN p
        """
    }
# execute query
def execute_query(state):
    result = graph.query(state["cypher_query"])

    cleaned = [r["result"] for r in result]

    return {**state, "result": cleaned}
# answer
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
# build graph
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
# display graph
from IPython.display import Image, display

# display(Image(compiled_graph.get_graph().draw_mermaid_png()))

# testing
# print(compiled_graph.invoke({
#     "question": "Which Cities lie in the administrative District of Münster?"
# }))

print(compiled_graph.invoke({
    "question": "In which federal State lies Selm?"
}))
# compiled_graph.invoke({
#     "question": "What Cities lie in Rhein-Sieg-Kreis?"
# })
# compiled_graph.invoke({
#     "question": "Which City is next to Siegburg?"
# })