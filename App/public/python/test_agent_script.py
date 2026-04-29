# Import und Setup
# Install (falls nötig)
# pip install langgraph langchain langchain-openai neo4j

from typing import TypedDict, Literal, Optional, Dict
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

    # 🌍 SPATIAL
    cardinal_direction: Optional[str]   # "north" | "south" | "east" | "west" | None

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
def safe_parse(response: str):
    import json

    try:
        data = json.loads(response)
    except Exception:
        # Fallback
        return {
            "intent": "within",
            "entity_name": "",
            "cardinal_direction": None,
            "distance_filter": None
        }

    # ✅ Mandatory fields
    data.setdefault("intent", "within")
    data.setdefault("entity_name", "")

    # ✅ Spatial Queries
    data.setdefault("cardinal_direction", None)
    data.setdefault("distance_filter", None)

    # ✅ Normalisation

    # ensure intent
    if data["intent"] not in ["within", "touches", "relates"]:
        data["intent"] = "within"

    # normalise direction
    if data.get("cardinal_direction"):
        dir_raw = data["cardinal_direction"].lower()

        mapping = {
            # north
            "north": "northern",

            # south
            "south": "southern",

            # east
            "east": "eastern",

            # west
            "west": "western",

            # diagonals
            "northeast": "northeastern",
            "northwest": "northwestern",
            "southeast": "southeastern",
            "southwest": "southwestern"
        }

        data["cardinal_direction"] = mapping.get(dir_raw, dir_raw)

    # ensure distance 
    if data.get("distance_filter"):
        df = data["distance_filter"]

        if isinstance(df, dict):
            # Validation
            data["distance_filter"] = {
                "operator": df.get("operator"),
                "value": df.get("value"),
                "unit": df.get("unit")
            }

            # optional: if empty -> None
            if all(v is None for v in data["distance_filter"].values()):
                data["distance_filter"] = None

        else:
            data["distance_filter"] = None
    return data
    
# Interpret Query
def interpret_query(state):
    prompt = f"""

    Question:
    {state['question']}

    Return ONLY valid JSON with this schema:
    {{
    "intent": "within | touches | relates",
    "entity_name": "...",
    "cardinal_direction": "northern | southern | eastern | western | northeastern | northwestern | southeastern | southwestern | null",
    "distance_filter": {{
        "operator": "< | > | = | <= | >= | null",
        "value": number | null,
        "unit": "km | m | null"
    }}
    }}


    1. Classify the question into one of these intents:

    - "within": hierarchical containment (lies in, belongs to, is in)
    - "touches": geographic neighbors (lies next to, is next to, touches)
    - "relates": generic relation, cardinal direction or distance (how far, north/south/east/west)

    2. Find out the entity name. The entity name is the name of a place in Germany.

    Rules:
    - "lies in", "in which ..." → ALWAYS "within"
    - "Which ... lie in ..." → ALWAYS "within"

    - "next to", "border ..." → ALWAYS "touches"

    - "relates" → ALWAYS "relates"
    - "What lies north/south/east/west of ...?" → ALWAYS "relates"
    - "How far ..." → ALWAYS "relates"

    -The name of the entity is NEVER a word like: 
    - "City", "Cities",
    - "District", "Districts"
    - "Administrative", "federal", "State"

    3. For intent = "relates":
        3.1. cardinal_direction:
        - Extract if mentioned ("northern | southern | eastern | western | northeastern | northwestern | southeastern | southwestern)
        - "north", "northern" → ALWAYS cardinal_direction = "northern"
        - "south", "southern" → ALWAYS cardinal_direction = "southern"
        - "east", "eastern" → ALWAYS cardinal_direction = "eastern"
        - "west", "western" → ALWAYS cardinal_direction = "western"
        - "northeast", "northeastern" → ALWAYS cardinal_direction = "northeastern"
        - "northwest", "northwestern" → ALWAYS cardinal_direction = "northwestern"
        - "southeast", "southeastern" → ALWAYS cardinal_direction = "southeastern"
        - "southwest", "southwestern" → ALWAYS cardinal_direction = "southwestern"
        - Otherwise return null

        3.2. distance_filter:
        - Extract ONLY if a distance constraint is mentioned
        - Convert all numbers to numeric values (no strings)
        - Normalize units:
        - "km", "kilometer" → km
        - "m", "meter" → m

        3.3. operator mapping:
        - "less than", "unter", "weniger als" → "<"
        - "more than", "über", "mehr als" → ">"
        - "within", "max", "höchstens" → "<="
        - "exactly", "genau" → "="

    """

    response = llm.invoke(prompt).content
    parsed = safe_parse(response)
    return {
            **state,
            "intent": parsed.get("intent"),
            "entity_name": parsed.get("entity_name"),
            "cardinal_direction": parsed.get("cardinal_direction"),
            "distance_filter": parsed.get("distance_filter")
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
    # ✅ Case 1: one result
    if len(types) == 1:
        return {**state, "source_type": types[0]}
    
    if not results:
        return {**state, "source_type": "District"}  # or None?

    # ✅ Case 2: several results → LLM
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
- If intent = "within":
    - If a Type ("City | District | AdministrativeDistrict | FederalState") is stated in the question like in the following examples:
        - If "administrative District of" or "the administrative District ..." is in the question → the source type = AdministrativeDistrict
        - If "District of" or "the District ..." is in the question → the source type = District
        - If "federal State of" or "the federal State ..." is in the question → the source type = FederalState
    use them as source type in every case

    - If asking "Which Cities lie within ..." → the source type must be: "District" or "AdministrativeDistrict" or "FederalState"
    - If asking "Which Districts lie within ..." → the source type must be: "AdministrativeDistrict" or "FederalState"
    - If asking "Which administrative Districts lie within ..." → the source type must be: "FederalState"

- If intent = "touches":
    - If asking "Which Cities lie next to (border) ..." → source type = "City"
    - If asking "Which administrative Districts lie next to (border) ..." → source type =  "AdministrativeDistrict"
    - If asking "Which Districts lie next to (border) ..." → source type = "District"
    - If asking "Which federal States lie next to (border) ..." → "FederalState"
    - If "touches" → same level entities

- If intent = "relates":

Return ONLY JSON:
{{
  "source_type": "City | District | AdministrativeDistrict | FederalState"
}}
"""

    response = llm.invoke(prompt).content

    parsed = safe_parse(response)

    source_type = parsed.get("source_type")

    # fallback
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
        MATCH 
        (start:{state['source_type']} {{Name: '{state['entity_name']}'}})
        -[:hasFootprint]->(:Geometry)
        <-[:touches]-(:Geometry)
        <-[:hasFootprint]-(neighbor:{state['source_type']})

        RETURN DISTINCT neighbor.Name AS result
        """
    }
# relates
def build_relates_query(state):
    cardinal_direction = state.get("cardinal_direction")
    distance = state.get("distance_filter")

    where_clauses = []
    rel_props = []

    # Cardinal Direction
    if cardinal_direction:
        rel_props.append(f"Spatial_relation: '{cardinal_direction}'")

    # build relation
    rel_filter = ""
    if rel_props:
        rel_filter = "{" + ", ".join(rel_props) + "}"

    # Distance
    if distance:
        where_clauses.append(f"r.Distance_between {distance['operator']} {distance['value']}")

    where_stmt = ""
    if where_clauses:
        where_stmt = "WHERE " + " AND ".join(where_clauses)

    query = f"""
    MATCH 
    (start:{state['source_type']} {{Name: '{state['entity_name']}'}})
    -[:hasFootprint]->(g1:Geometry)
    -[r:relates {rel_filter}]->(g2:Geometry)
    <-[:hasFootprint]-(other:{state['source_type']})

    {where_stmt}

    RETURN DISTINCT other.Name AS result
    """
    return {
        **state,
        "cypher_query": query
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
#from IPython.display import Image, display
# display(Image(compiled_graph.get_graph().draw_mermaid_png()))

# testing

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