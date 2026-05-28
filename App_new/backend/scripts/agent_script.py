# Import und Setup
# Install
# pip install langgraph langchain langchain-openai neo4j

from typing import TypedDict, Literal, Optional, Dict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_community.graphs import Neo4jGraph
from langchain_neo4j import Neo4jGraph

from rich.console import Console
from rich.panel import Panel
from rich.json import JSON

import json
import re

import os

from typing import List
from pydantic import BaseModel, Field, field_validator

from dotenv import load_dotenv
load_dotenv()  # Loads env variables from .env file

import spatial_relation_functions as srf

#llm = None
graph = None


# function only executed once when starting the app
def init_db():
    global graph
    graph = Neo4jGraph(
        url="neo4j://localhost:7687",
        username="neo4j",
        password="chatwithgermany"
    )

init_db()

# Pydantic and llm_with_structured_output

relationship_description = """
Classify the question into one of these spatial_relationships:
    - "location": the geographic position (Where lies, Where is located), no cardinal direction or distance constraint mentioned
    - "within": hierarchical containment (lies in, belongs to, is in), only if NO number/distance constraint is mentioned
    - "touches": geographic neighbors (lies next to, is next to, touches)
    - "relates": generic relation, cardinal direction or distance (how far, north/south/east/west)
    - "None": if none of the above apply
"""

cardinal_direction_description = """
Extract one of the following relationships if mentioned ("northern | southern | eastern | western | northeastern | northwestern | southeastern | southwestern)
    - "north", "northern" → ALWAYS cardinal_direction = "northern"
    - "south", "southern" → ALWAYS cardinal_direction = "southern"
    - "east", "eastern" → ALWAYS cardinal_direction = "eastern"
    - "west", "western" → ALWAYS cardinal_direction = "western"
    - "northeast", "northeastern" → ALWAYS cardinal_direction = "northeastern"
    - "northwest", "northwestern" → ALWAYS cardinal_direction = "northwestern"
    - "southeast", "southeastern" → ALWAYS cardinal_direction = "southeastern"
    - "southwest", "southwestern" → ALWAYS cardinal_direction = "southwestern"
"""

distance_constraint_description = """
    - Return a float value representing the distance constraint
    - Convert all numbers to numeric values (no strings)
    - Calculate the distance constraint in meters (m)
    - Normalize units:
        - "km", "kilometer" → km
        - "m", "meter" → m
"""

distance_between_description = """
    - TRUE only if TWO entities are explicitly compared
    - keywords: "between", "distance from X to Y", "What is the distance.."
"""

radius_description = """
    - TRUE only if the question explicitly states a radius or distance constraint without comparing two entities
    - Keywords: "within a radius of X km/m", "in a radius of X km/m", "within X km/m distance", "in X km/m distance", "X km/m from", "X km/m around", "X km/m near", "X km/m close to"
"""

hierarchy_assignment_description = """
    - Assign the entities to one of the following hierarchies:
    City < District < AdministrativeDistrict < FederalState

    - Always return the answer as a NON EMPTY list of lists of the format [[entity_name, hierarchy],[...]]

    Rules:
    - If a Type ("City | AdministrativeDistrict | District | FederalState") is stated in the question like in the following examples:
        - If "administrative District of" or "the administrative District ..." is in the question → [entity_name, "AdministrativeDistrict"]
        - If "District of" or "the District ..." is in the question → [entity_name, "District"]
        - If "federal State of" or "the federal State ..." is in the question → [entity_name, "FederalState"]

        - If asking "Which Cities lie within ..." → [entity_name, "District"] or [entity_name, "AdministrativeDistrict"] or [entity_name, "FederalState"]
        - If asking "Which Districts lie within ..." → [entity_name, "AdministrativeDistrict"] or [entity_name, "FederalState"]
        - If asking "Which administrative Districts lie within ..." → [entity_name, "FederalState"]

        - If asking "Which Cities lie next to (border) ..." → [entity_name, "City"]
        - If asking "Which administrative Districts lie next to (border) ..." → [entity_name, "AdministrativeDistrict"]
        - If asking "Which Districts lie next to (border) ..." → [entity_name, "District"]
        - If asking "Which federal States lie next to (border) ..." → [entity_name, "FederalState"]
    - If no type is stated assign the type "City" or, if the following german words are in the name, use them:
        - If "Stadt" in the name → "City"
        - If "Kreis" in the name → "District"
        - If "Regierungsbezirk" in the name → "AdministrativeDistrict"
        - If "Bundesland" in the name → "FederalState"
"""

spatial_entities_description = """
     REQUIRED: Always return a list of entity names mentioned in the question.
     - A entity name is a proper name of a place in Germany
     - Do NOT include the type ("City", "District", "AdministrativeDistrict", "FederalState")
     of an entity into the list
"""

target_type_description = """
    assign the target entity type in a geographic query to one of the following hierarchy:
    City < District < AdministrativeDistrict < FederalState

    - Return the answer as a list of strings

    Rules:
    - The target type is what is asked for in the question
"""

class ParameterExtraction(BaseModel):
    language: str = Field(description="language of the input question")
    spatial_relationship: str = Field(description=relationship_description)
    cardinal_direction: Optional[str] = Field(default=None, description=cardinal_direction_description)
    spatial_entities: List[str] = Field(description=spatial_entities_description)  # NEVER empty!
    distance_constraint: Optional[float] = Field(default=None, description=distance_constraint_description)
    radius: Optional[bool] = Field(default=False, description=radius_description)
    distance_between: bool = Field(description=distance_between_description)
    hierarchy: Optional[List[List[str]]] = Field(default=None, description=hierarchy_assignment_description)
    target_type: str = Field(description=target_type_description)

    # Validators for checking if the variables fit the model (and corrections if necessary)

    # String fields: List → first element
    @field_validator(
        'language', 'spatial_relationship', 'cardinal_direction', 'target_type',
        mode='before'
    )
    @classmethod
    def coerce_list_to_string(cls, v):
        if isinstance(v, list):
            return str(v[0]) if len(v) > 0 else ""
        if v is None:
            return ""
        return v

    # spatial_entities: String → List
    @field_validator('spatial_entities', mode='before')
    @classmethod
    def coerce_string_to_list(cls, v):
        if isinstance(v, str):
            return [v] if v else []
        if v is None:
            return []
        return v

    # hierarchy: normalize different formats
    @field_validator('hierarchy', mode='before')
    @classmethod
    def normalize_hierarchy(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [[v]] if v else []
        if isinstance(v, list):
            if len(v) == 0:
                return []
            if all(isinstance(item, str) for item in v):
                return [v]
            return [
                [str(x) for x in sublist] if isinstance(sublist, list) else [str(sublist)]
                for sublist in v
            ]
        return v

    # distance_constraint: String/None → float
    @field_validator('distance_constraint', mode='before')
    @classmethod
    def coerce_to_float(cls, v):
        if v is None or v == "":
            return 0.0
        if isinstance(v, list):
            v = v[0] if v else 0.0
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    # Bool-Fields: String "true"/"false" → True/False
    @field_validator('radius', 'distance_between', mode='before')
    @classmethod
    def coerce_to_bool(cls, v):
        if isinstance(v, bool):
            return v
        if v is None:
            return False
        if isinstance(v, list):
            v = v[0] if v else False
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'ja')
        return bool(v)


class AgentState(TypedDict):
    # INPUT
    question: str
    apiKey: str
    selectedModel: str

    # Parameters
    language: str
    spatial_relationship: str
    cardinal_direction: Optional[str]
    distance_between: bool
    spatial_entities: str
    distance_constraint: Optional[float]
    radius: bool
    hierarchy: Optional[List[List[str]]]
    target_type: str
    route: str

    # OUTPUT
    cypher_query: str
    result: str

# Hierarchy
HIERARCHY = [
    "City",
    "District",
    "AdministrativeDistrict",
    "FederalState"
]

def get_llm_config(model_name, api_key):
    """Sets the base URL depending on the provider."""
    # OpenAI-Models start with "gpt-"
    if model_name.startswith("gpt-"):
        return {
            "openai_api_key": api_key,
            "model": model_name,
            "temperature": 1,
        }
    else:
        # SAIA / GWDG
        return {
            "openai_api_key": api_key,
            "model": model_name,
            "temperature": 1,
            "base_url": "https://chat-ai.academiccloud.de/v1",
        }

# JSON Extraction from LLM Responses (for SAIA Models)
def extract_json_from_text(text: str):
    """Extrahiert ein JSON-Objekt aus einer (möglicherweise gewrappten) LLM-Antwort."""
    if not text:
        return None
    
    text = text.strip()
    
    # Plain JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # ```json ... ``` Code-Block
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Match on {...}
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    
    return None


# Manual Prompting for SAIA Models
def extract_parameters_manually(question: str) -> ParameterExtraction:
    """
    Manual prompting for SAIA models that do not support native 
    structured output or exhibit tool-calling behavior.
    """
    global llm
    
    prompt = f"""You are a JSON data extractor. Do NOT call any function. Do NOT use tools.
Just return a plain JSON object describing the question parameters.

QUESTION: "{question}"

Return ONLY a JSON object with EXACTLY these fields. No markdown, no code blocks, no explanations:

{{
  "language": "English",
  "spatial_relationship": "within",
  "cardinal_direction": "",
  "spatial_entities": ["EntityName"],
  "distance_constraint": 0,
  "radius": false,
  "distance_between": false,
  "hierarchy": [["EntityName", "City"]],
  "target_type": "District"
}}

FIELD RULES:
- "language": Language of the question ("English", "German", etc.)
- "spatial_relationship": ONE of:
    "location" (Where lies, Where is located),
    "within" (lies in, belongs to, is in),
    "touches" (next to, borders),
    "relates" (how far, direction, distance),
    "None" (none of the above)
- "cardinal_direction": ONE of "northern", "southern", "eastern", "western",
    "northeastern", "northwestern", "southeastern", "southwestern", or ""
- "spatial_entities": List of place names mentioned in the question (without type)
- "distance_constraint": Distance in METERS as float (km → multiply by 1000). 0 if no distance.
- "radius": true ONLY if "within X km radius" or similar is mentioned
- "distance_between": true ONLY if asking distance BETWEEN two entities
- "hierarchy": List of [entity_name, type] pairs.
    Type is one of: "City", "District", "AdministrativeDistrict", "FederalState"
- "target_type": What the question asks for. ONE of:
    "City", "District", "AdministrativeDistrict", "FederalState"

EXAMPLES:

Q: "In which district lies Bocholt?"
{{"language":"English","spatial_relationship":"within","cardinal_direction":"","spatial_entities":["Bocholt"],"distance_constraint":0,"radius":false,"distance_between":false,"hierarchy":[["Bocholt","City"]],"target_type":"District"}}

Q: "What is the distance between Bonn and Cologne?"
{{"language":"English","spatial_relationship":"relates","cardinal_direction":"","spatial_entities":["Bonn","Cologne"],"distance_constraint":0,"radius":false,"distance_between":true,"hierarchy":[["Bonn","City"],["Cologne","City"]],"target_type":"City"}}

Q: "Which cities are within 10 km of Bonn?"
{{"language":"English","spatial_relationship":"relates","cardinal_direction":"","spatial_entities":["Bonn"],"distance_constraint":10000,"radius":true,"distance_between":false,"hierarchy":[["Bonn","City"]],"target_type":"City"}}

Q: "Which administrative districts border Düsseldorf?"
{{"language":"English","spatial_relationship":"touches","cardinal_direction":"","spatial_entities":["Düsseldorf"],"distance_constraint":0,"radius":false,"distance_between":false,"hierarchy":[["Düsseldorf","AdministrativeDistrict"]],"target_type":"AdministrativeDistrict"}}

Q: "Which cities lie northern of Münster?"
{{"language":"English","spatial_relationship":"relates","cardinal_direction":"northern","spatial_entities":["Münster"],"distance_constraint":0,"radius":false,"distance_between":false,"hierarchy":[["Münster","City"]],"target_type":"City"}}

Now respond for: "{question}"
Return ONLY the JSON object, nothing else:"""

    # Direct llm.invoke - no structured_output, no tools
    raw = llm.invoke(prompt).content
    print(f"Raw SAIA response: {raw[:500]}")
    
    parsed = extract_json_from_text(raw)
    
    if not parsed:
        raise ValueError(f"Could not extract JSON from SAIA response: {raw[:500]}")
    
    print(f"Parsed JSON: {parsed}")
    
    # Defaults for missing fields
    defaults = {
        "language": "English",
        "spatial_relationship": "None",
        "cardinal_direction": "",
        "spatial_entities": [],
        "distance_constraint": 0.0,
        "radius": False,
        "distance_between": False,
        "hierarchy": [],
        "target_type": "City",
    }
    
    # If the model returns a tool call format: convert
    if isinstance(parsed, dict) and parsed.get("type") == "function":
        print("Model returned tool-call format, attempting conversion")
        params = parsed.get("parameters", {}) or parsed.get("arguments", {})
        city = params.get("city") or params.get("name") or params.get("entity")
        if city:
            defaults["spatial_entities"] = [city]
            defaults["hierarchy"] = [[city, "City"]]
            defaults["spatial_relationship"] = "within"
            func_name = (parsed.get("name") or "").lower()
            if "district" in func_name and "administrative" not in func_name:
                defaults["target_type"] = "District"
            elif "administrative" in func_name:
                defaults["target_type"] = "AdministrativeDistrict"
            elif "state" in func_name or "federal" in func_name:
                defaults["target_type"] = "FederalState"
            elif "city" in func_name or "cities" in func_name:
                defaults["target_type"] = "City"
            else:
                defaults["target_type"] = "District"
        parsed = defaults
    else:
        # Standard JSON: Merge with defaults
        parsed = {**defaults, **parsed}
    
    return ParameterExtraction(**parsed)


# Interpret Query with Provider-Splitting
def interpret_query(state):
    question = state['question']
    api_key = state['apiKey']
    model_name = state['selectedModel']

    # initialize LLM
    global llm

    config = get_llm_config(model_name, api_key)
    llm = ChatOpenAI(**config)

    # TWO COMPLETELY SEPARATE PATHS
    if model_name.startswith("gpt-"):
        # OpenAI: native function_calling works
        print(f"Using OpenAI structured output for {model_name}")
        structured_llm = llm.with_structured_output(
            schema=ParameterExtraction,
            method="function_calling"
        )
        response = structured_llm.invoke(question)
    else:
        # SAIA: manual Prompting (avoids tool-calling issues)
        print(f"Using manual prompting for SAIA model {model_name}")
        response = extract_parameters_manually(question)

    if response.spatial_relationship == "None":
        return {
            **state,
            "result": None,
            "route": "verbalize"
        }

    return {
        **state,
        "language": response.language,
        "spatial_relationship": response.spatial_relationship,
        "cardinal_direction": response.cardinal_direction,
        "distance_between": response.distance_between,
        "radius": response.radius,
        "spatial_entities": response.spatial_entities,
        "distance_constraint": response.distance_constraint,
        "hierarchy": response.hierarchy,
        "target_type": response.target_type,
        "route": "add_inheritance"
    }


# Inheritance
def add_inheritance(state):
    source = get_source_type(state)
    target = state.get("target_type", "City")

    
    if source not in HIERARCHY or target not in HIERARCHY:
        inheritance = "sub_class"
    else:
        s = HIERARCHY.index(source)
        t = HIERARCHY.index(target)

        if s > t:
            inheritance = "sub_class"
        elif s < t:
            inheritance = "super_class"
        else:
            inheritance = "same"
    return {
        **state,
        "inheritance": inheritance
    }

# Routing
def select_query_type(state):
    if state["spatial_relationship"] == "within":
        return f"within_{state['inheritance']}"

    return f"{state['spatial_relationship']}_action"

def get_source_type(state, fallback="City"):
    """Secure access to the source type from the hierarchy."""
    hierarchy = state.get("hierarchy", [])
    if not hierarchy or not hierarchy[0]:
        return fallback
    first = hierarchy[0]
    # Expected: [name, type] – use index 1 or fallback
    if isinstance(first, list) and len(first) >= 2:
        type_str = first[1]
        return type_str if type_str in HIERARCHY else fallback
    return fallback

def get_source_name(state, fallback=""):
    """Reliable access to the source name from the hierarchy."""
    hierarchy = state.get("hierarchy", [])
    if not hierarchy or not hierarchy[0]:
        # Fallback from spatial_entities
        entities = state.get("spatial_entities", [])
        return entities[0] if entities else fallback
    first = hierarchy[0]
    if isinstance(first, list) and len(first) >= 1:
        return first[0]
    return fallback


def build_location_query(state):
    source = get_source_type(state)
    name = get_source_name(state)

    query = f"""
    MATCH (start:{source} {{Name: '{name}'}})

    OPTIONAL MATCH (start)-[:hasFootprint]->(g:Geometry)

    OPTIONAL MATCH path =
        (start)-[:hasFootprint]->(:Geometry)
        -[:within*1..]->(:Geometry)
        <-[:hasFootprint]-(parent)

    WITH start, g, collect(DISTINCT {{
        id: parent.ID,
        name: parent.Name
    }}) AS target

    RETURN {{
        start: {{
            id: start.ID,
            name: start.Name,
            centroid: start.Centroid
        }},
        target: target
    }} AS result
    """
    return {**state, "cypher_query": query}

# Within
def build_within_super_class(state):
    source = get_source_type(state)
    target = state["target_type"]
    name = get_source_name(state)

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

    query += f"""
    WITH start, collect(DISTINCT {{
        id: {current}.ID,
        name: {current}.Name
    }}) AS target

    RETURN {{
        start: {{
            id: start.ID,
            name: start.Name
        }},
        target: target
    }} AS result
    """
    return {**state, "cypher_query": query}

def build_within_sub_class(state):
    source = get_source_type(state)
    target = state["target_type"]
    name = get_source_name(state)

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

    query += f"""
    WITH start, collect(DISTINCT {{
        id: {current}.ID,
        name: {current}.Name
    }}) AS target

    RETURN {{
        start: {{
            id: start.ID,
            name: start.Name
        }},
        target: target
    }} AS result
    """
    return {**state, "cypher_query": query}

# touches
def build_touches_query(state):
    source = get_source_type(state)
    name = get_source_name(state)

    return {
        **state,
        "cypher_query": f"""
        MATCH 
        (start:{source} {{Name: '{name}'}})
        -[:hasFootprint]->(:Geometry)
        <-[:touches]-(:Geometry)
        <-[:hasFootprint]-(neighbor:{source})

        WITH start, collect(DISTINCT {{
            id: neighbor.ID,
            name: neighbor.Name
        }}) AS target

        RETURN {{
            start: {{
                id: start.ID,
                name: start.Name
            }},
            target: target
        }} AS result
        """
    }

# relates
def select_relates_type(state):
    if state["distance_between"] == True:
        return "distance_between"

    if state["radius"] == True:
        return "radius"

    if state.get("cardinal_direction"):
        return "direction"

    # Fallback when the model returned a distance constraint
    # but did not explicitly set radius=True.
    if state.get("distance_constraint", 0) > 0:
        print("Radius was manually set to True based on distance_constraint")
        return "radius"

    return "direction"

def add_relates_type(state):
    return {
        **state,
        "relates_type": select_relates_type(state)
    }


def build_direction_query(state):
    direction = state.get("cardinal_direction")
    source = get_source_type(state)
    name = get_source_name(state)

    rel_filter = ""
    if direction:
        rel_filter = f"{{Spatial_relation: '{direction}'}}"

    query = f"""
    MATCH 
    (start:{source} {{Name: '{name}'}})
    -[:hasFootprint]->(g1:Geometry)
    -[r:relates {rel_filter}]->(g2:Geometry)
    <-[:hasFootprint]-(other:{source})

    WITH start, collect(DISTINCT {{
        id: other.ID,
        name: other.Name
    }}) AS target

    RETURN {{
        start: {{
            id: start.ID,
            name: start.Name
        }},
        target: target
    }} AS result
    """
    return {**state, "cypher_query": query}


def build_radius_query(state):
    distance = state["distance_constraint"]
    source = get_source_type(state)
    name = get_source_name(state)

    query = f"""
    MATCH 
    (start:{source} {{Name: '{name}'}})
    -[:hasFootprint]->(g1:Geometry)
    -[r:relates]->(g2:Geometry)
    <-[:hasFootprint]-(other:{source})

    WHERE r.Distance_between <= {distance}

    WITH start, collect(DISTINCT {{
        id: other.ID,
        name: other.Name
    }}) AS target

    RETURN {{
        start: {{
            id: start.ID,
            name: start.Name
        }},
        target: target
    }} AS result
    """
    return {**state, "cypher_query": query}


def build_distance_between_query(state):
    entities = state.get("spatial_entities", [])
    source = get_source_type(state)
    
    if len(entities) < 2:
        return {**state, "cypher_query": "RETURN null AS result LIMIT 0"}
    
    e1 = entities[0]
    e2 = entities[1]

    query = f"""
    MATCH 
    (a:{source} {{Name: '{e1}'}})
    -[:hasFootprint]->(g1:Geometry)
    -[r:relates]->(g2:Geometry)
    <-[:hasFootprint]-(b:{source} {{Name: '{e2}'}})

    WITH a,r, collect(DISTINCT {{
        id: b.ID,
        name: b.Name
    }}) AS target

    RETURN {{
        start: {{
            id: a.ID,
            name: a.Name
        }},
        target: target
    }} AS result
    """
    return {**state, "cypher_query": query}

# execute query
def execute_query(state):
    global graph
    result = graph.query(state["cypher_query"])
    cleaned = [r["result"] for r in result]

    # adds the distance to the result (only works with two entities)
    if state["distance_between"] == True:
        cleaned = srf.calculate_distances(cleaned)

    return {**state, "result": cleaned}

# answer
def verbalize(state):
    prompt = f"""
Turn the result into natural english based on the context of the question.

Question: {state['question']}
Result: {state['result']}

Rules:
- If the result is a number, it is a Distance in m. Round it to km
- The first letter of the id states which hierarchy level the result has:
    - C = City
    - D = District
    - A = Administrative District
    - F = Federal State
  include the level in the answer but NOT the id

- If the result is empty answer:
    "Hello. This chatbot answers only questions about the geometries of Germany. Please try again with a different question."
- The Result is never a question
- Put only the result in the Answer NEVER the question
- Do not use Markdown or code formatting in the answer, just plain text
"""
    if state['result'] is None or (isinstance(state['result'], list) and len(state['result']) == 0):
        return {
            **state,
            "result": {
                "verbalized": llm.invoke(prompt).content,
                "start": None,
                "target": None,
            }
        }

    return {
        **state,
        "result": {
            "verbalized": llm.invoke(prompt).content,
            "start": state["result"][0].get("start"),
            "target": state["result"][0].get("target"),
        }
    }

# build graph
workflow = StateGraph(AgentState)

workflow.add_node("interpret_query", interpret_query)
workflow.add_node("add_inheritance", add_inheritance)

workflow.add_node("build_location_query", build_location_query)
workflow.add_node("build_within_super_class", build_within_super_class)
workflow.add_node("build_within_sub_class", build_within_sub_class)
workflow.add_node("build_touches_query", build_touches_query)
workflow.add_node("add_relates_type", add_relates_type)

# relates
workflow.add_node("build_direction_query", build_direction_query)
workflow.add_node("build_radius_query", build_radius_query)
workflow.add_node("build_distance_between_query", build_distance_between_query)

workflow.add_node("execute_query", execute_query)
workflow.add_node("verbalize", verbalize)

workflow.add_edge(START, "interpret_query")

workflow.add_conditional_edges(
    "interpret_query",
    lambda state: state.get("route"),
    {
        "verbalize": "verbalize",
        "add_inheritance": "add_inheritance"
    }
)

workflow.add_conditional_edges(
    "add_inheritance",
    select_query_type,
    {
        "location_action": "build_location_query",
        "within_super_class": "build_within_super_class",
        "within_sub_class": "build_within_sub_class",
        "touches_action": "build_touches_query",
        "relates_action": "add_relates_type"
    }
)

# relates sub-routing
workflow.add_conditional_edges(
    "add_relates_type", 
    select_relates_type,
    {
        "direction": "build_direction_query",
        "radius": "build_radius_query",
        "distance_between": "build_distance_between_query"
    }
)

workflow.add_edge("build_location_query", "execute_query")
workflow.add_edge("build_within_super_class", "execute_query")
workflow.add_edge("build_within_sub_class", "execute_query")
workflow.add_edge("build_touches_query", "execute_query")
workflow.add_edge("build_direction_query", "execute_query")
workflow.add_edge("build_radius_query", "execute_query")
workflow.add_edge("build_distance_between_query", "execute_query")

workflow.add_edge("execute_query", "verbalize")
workflow.add_edge("verbalize", END)

compiled_graph = workflow.compile()


console = Console()

def fancy_print(result):
    console.print(Panel.fit(
        f"[bold cyan]QUESTION[/bold cyan]\n{result.get('question')}",
        border_style="cyan"
    ))

    console.print(Panel.fit(
        f"[bold green]ANSWER[/bold green]\n{result.get('result')['verbalized']}",
        border_style="green"
    ))

    console.print("[bold yellow]FULL OUTPUT[/bold yellow]")
    console.print(JSON.from_data(result))

    console.print("\n" + "═"*80 + "\n")

def run_question(question: str, apiKey: str, selectedModel: str):
    """Execute the question using the graph."""
    inputs = {
        "question": question, 
        "apiKey": apiKey, 
        "selectedModel": selectedModel
    }
    return compiled_graph.invoke(inputs)


def run_all(question: str, apiKey: str):
    return run_question(question, apiKey)


if __name__ == "__main__":
    example_question = "What lies eastern from Bocholt?"
    example_api_key = os.getenv("OPENAI_API_KEY")
    if example_api_key:
        result = run_question(example_question, example_api_key, "gpt-5-nano")

        fancy_print(result)
    else:
        print("Please set OPENAI_API_KEY before running the script directly.")