import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import und Setup
# Install
# pip install langgraph langchain langchain-openai neo4j

from typing import TypedDict, Literal, Optional, Dict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_community.graphs import Neo4jGraph
from langchain_neo4j import Neo4jGraph

from rich.console import Console
from rich.panel import Panel
from rich.json import JSON

import json
import re

import os

from typing import List
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()  # Loads env variables from .env file

from typing import Literal

try:
    from . import spatial_relation_functions as srf
except (ImportError, SystemError):
    # Allow running this file directly for local debugging:
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

instructions = """Analyze the input query and extract the following parameters.

<language>
  <task>extract the language of the query</task>
</language>

<relationship>
  <task>extract the type of relationship mentioned in the query</task>
  <constraints>
    - The relationship can only be one of the following:
      - "location": the geographic position (Where lies, Where is located), no cardinal direction or distance constraint mentioned
      - "within": hierarchical containment (lies in, belongs to, is in), only if NO number/distance constraint is mentioned
      - "touches": geographic neighbors (lies next to, is next to, touches)
      - "relates": generic relation, cardinal direction or distance (how far, north/south/east/west)
      - "None": if none of the above apply
  </constraints>
</relationship>

<cardinal_direction>
<task>extract one of the following relationships if mentioned ("northern | southern | eastern | western | northeastern | northwestern | southeastern | southwestern)</task>
  <constraints>
    - "north", "northern" → ALWAYS cardinal_direction = "northern"
    - "south", "southern" → ALWAYS cardinal_direction = "southern"
    - "east", "eastern" → ALWAYS cardinal_direction = "eastern"
    - "west", "western" → ALWAYS cardinal_direction = "western"
    - "northeast", "northeastern" → ALWAYS cardinal_direction = "northeastern"
    - "northwest", "northwestern" → ALWAYS cardinal_direction = "northwestern"
    - "southeast", "southeastern" → ALWAYS cardinal_direction = "southeastern"
    - "southwest", "southwestern" → ALWAYS cardinal_direction = "southwestern"
  </constraints>
</cardinal_direction>

<distance_constraint>
  <task>Return a float value representing the distance constraint. ONLY if a distance constraint is mentioned in the query. </task>
  <constraints>
    - Convert all numbers to numeric values (no strings)
    - Calculate the distance constraint in meters (m)
    - Normalize units:
        - "km", "kilometer" → km
        - "m", "meter" → m
   </constraints>
</distance_constraint>

<distance_between>
  <task>return TRUE only if TWO entities are explicitly compared</task>
  <constraints>
    - relevant keywords for TRUE: "between", "distance from X to Y", "What is the distance.."
  </constraints>
</distance_between>

<radius>
  <task>return TRUE only if the question explicitly states a radius or distance constraint without comparing two entities</task>
  <constraints>
    - relevant keywords for TRUE: "within a radius of X km/m", "in a radius of X km/m", "within X km/m distance", "in X km/m distance", "X km/m from", "X km/m around", "X km/m near", "X km/m close to"
  </constraints>
</radius>

<hierarchy>
<task>assign the entities to one of the following hierarchies:</task>
  <constraints>
    - allowed hierarchy values:
        - "City",
        - "AdministrativeCommunity",
        - "District",
        - "AdministrativeDistrict",
        - "FederalState"
    - Return one item for every entity in the question.
    - Explicit type in question overrides defaults.
    - Default hierarchy is City.
    - German keywords:
        - Stadt -> City
        - Verwaltungsgemeinschaft -> AdministrativeCommunity
        - Kreis -> District
        - Regierungsbezirk -> AdministrativeDistrict
        - Bundesland -> FederalState
  </constraints>
</hierarchy>

<spatial_entities>
  <task>Return a list of entity names mentioned in the question.</task>
  <constraints>
    - A entity name is a proper name of a place in Germany
    - It can be written in another language
    - If the name is in a different language than German, translate the name to German
      - (f.e. Cologne -> Köln, Munich -> München, Bavaria -> Bayern, Aix-la-Chapelle -> Aachen)
    - Do NOT include the type ("City", "District", "AdministrativeDistrict", "FederalState") of an entity into the list
  </constraints>
</spatial_entities>

<target_type>
  <task>Return the type of the target entity in the question.</task>
  <constraints>
    - Return one of the following types: 
        City < AdministrativeCommunity < District < AdministrativeDistrict < FederalState
    - Return the answer as a list of strings (there can be multiple target types in one question, e.g. "Which Cities and Districts lie within North Rhine-Westphalia?" → ["City", "District"])
    - The target type is what is asked for in the question
  </constraints>
</target_type>

Query: {query}

"""

class HierarchyItem(BaseModel):
    entity_name: str
    hierarchy: Literal[
        "City",
        "AdministrativeCommunity",
        "District",
        "AdministrativeDistrict",
        "FederalState"
    ]

class ParameterExtraction(BaseModel):
    language: str = Field(description="language of the input question")
    spatial_relationship: str = Field(description="type of relationship of interest in the question")
    cardinal_direction: str = Field(description="cardinal relationships in the input question")
    spatial_entities: List[str]  = Field(description="list of spatial entities in the input question")
    distance_constraint: str  = Field(description="distance constraints mentioned in the input question")
    radius: Optional[bool] = Field(default=False, description="whether or not the question implies a radius constraint")
    distance_between: str = Field(description="whether or not two entities are explicitly compared")
    hierarchy: List[HierarchyItem] = Field(default_factory=list, description="hierarchy assignment for the entities mentioned in the question")
    target_type: str = Field(description="the type of the target entity that is asked for in the question")

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
    hierarchy: List[HierarchyItem]
    target_type: str
    route: str

    # OUTPUT
    cypher_query: str
    result: str

# Hierarchy
HIERARCHY = [
    "City",
    "AdministrativeCommunity",
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
        prompt_template = PromptTemplate.from_template(instructions)
        chain = prompt_template | structured_llm
        response = chain.invoke(question)
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

    if not hierarchy:
        return fallback

    first = hierarchy[0]

    return (
        first.hierarchy
        if first.hierarchy in HIERARCHY
        else fallback
    )

def get_source_name(state, fallback=""):
    """Reliable access to the source name from the hierarchy."""
    hierarchy = state.get("hierarchy", [])

    if not hierarchy:
        entities = state.get("spatial_entities", [])
        return entities[0] if entities else fallback

    return hierarchy[0].entity_name


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

    query = f"""
        MATCH p = (start:{source} {{Name: '{name}'}})
        -[]->
        (:Geometry)
        -[:within*]->
        (g:Geometry)    
        <-[:hasFootprint]-
        ({target})
        """

    query += f"""
        WITH start, nodes(p) AS ns

        UNWIND ns AS n
        MATCH (obj)-[:hasFootprint]->(n)
        WHERE NOT obj:Geometry

        WITH start, collect(DISTINCT {{
            id: obj.ID,
            name: obj.Name
        }}) AS targets

        RETURN {{
            start: {{
                id: start.ID,
                name: start.Name
            }},
            target: targets
        }} AS result
        """
    return {**state, "cypher_query": query}

def build_within_sub_class(state):
    source = get_source_type(state)
    target = state["target_type"]
    name = get_source_name(state)


    query = f"""
        MATCH (start:{source} {{Name: '{name}'}})
        -[:hasFootprint]->
        (sourceGeom:Geometry)

        MATCH (target:{target})
        -[:hasFootprint]->
        (targetGeom:Geometry)

        MATCH (targetGeom)-[:within*]->(sourceGeom)

        WITH start, collect(DISTINCT {{
            id: target.ID,
            name: target.Name
        }}) AS targets

        RETURN {{
            start: {{
                id: start.ID,
                name: start.Name
            }},
            target: targets
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

    return "direction"

def add_relates_type(state):
    return {
        **state,
        "relates_type": select_relates_type(state)
    }


def build_direction_query(state):
    direction = state.get("cardinal_direction")
    name = get_source_name(state)
    source = get_source_type(state)

    # First get the ID of the source entity
    get_id_query = f"""
    MATCH (n:{source}) WHERE n.Name = "{name}" RETURN n.ID AS ID
    """
    records = graph.query(get_id_query)
    if not records or len(records) == 0:
        return {**state, "cypher_query": "RETURN null AS result LIMIT 0"}
    
    # Now calculate the cardinal direction query using the retrieved ID
    query = srf.calculate_cardinal_direction(records[0]["ID"], name, state["target_type"], direction)

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

    # Get the IDs of the source entity. The distance is then calculated later
    query = f"""
        MATCH 
            (n1:{source} {{Name: '{e1}'}}), 
            (n2:{source} {{Name: '{e2}'}})
        RETURN {{
            start: {{
                id: n1.ID,
                name: n1.Name
            }},
            target: [{{
                id: n2.ID,
                name: n2.Name
            }}]
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
Turn the result into natural language based on the context of the question.

Question: {state['question']}
Result: {state['result']}

Answer in this Language: {state['language']}

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
    example_question = "What is the distance between Siegburg and Hameln?"
    example_api_key = os.getenv("OPENAI_API_KEY")
    if example_api_key:
        result = run_question(example_question, example_api_key, "gpt-5-nano")

        fancy_print(result)
    else:
        print("Please set OPENAI_API_KEY before running the script directly.")