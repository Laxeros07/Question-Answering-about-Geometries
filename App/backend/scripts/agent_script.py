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
import threading
import time
import logging

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

def init_db():
    global graph

    graph = Neo4jGraph(
        url=os.getenv(
            "NEO4J_URI",
            "bolt://localhost:7687"
        ),
        username=os.getenv(
            "NEO4J_USER",
            "neo4j"
        ),
        password=os.getenv(
            "NEO4J_PASSWORD",
            "chatwithgermany"
        )
    )

# Start non-blocking connection attempts at import time
init_db()

instructions = """Analyze the input query and extract the following parameters.

<language>
  <task>extract the language of the query</task>
</language>

<relationship>
  <task>extract the type of relationship mentioned in the query. It can be a question or instruction like (show me/tell me) </task>
  <constraints>
    - The relationship can only be one of the following:
      - "location": the geographic position (Where lies, Where is located), no cardinal direction or distance constraint mentioned; show me "entity" in "entity" (when asked about a specific place)
      - "within": hierarchical containment (lies in, belongs to, is in), only if NO number/distance/radius constraint is mentioned
      - "touches": geographic neighbors, nearest/closest entities (lies next to, is next to, touches, located directly, directly next to, surrounded by) can include (north, south, east, west)
      - "relates": generic relation, cardinal direction or distance (how far, lies northern/southern/eastern/western of, lies (without "next to")) or radius
      - "None": if none of the above apply
      Example "touches": Which cities lie directly northern of Münster?
      Example "relates": Which cities lie northern of Münster?
  </constraints>
</relationship>

<cardinal_direction>
<task>extract one of the following relationships if mentioned ("northern | southern | eastern | western | northeastern | northwestern | southeastern | southwestern)</task>
  <constraints>
    - "north", "northern", "over" → ALWAYS cardinal_direction = "northern"
    - "south", "southern", "under" → ALWAYS cardinal_direction = "southern"
    - "east", "eastern", "right" → ALWAYS cardinal_direction = "eastern"
    - "west", "western", "left" → ALWAYS cardinal_direction = "western"
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
    - the relationship has to be "relates"
  </constraints>
</radius>

<spatial_entities>
  <task>Return a list of entity names mentioned in the question.</task>
  <constraints>
    - A entity name is a proper name of a place in Germany or the state Germany itself
    - It can be written in another language
    - If the name is in a different language than German, translate the name to German
      - (e.g. Germany -> Deutschland, Cologne -> Köln, Munich -> München, Bavaria -> Bayern, Aix-la-Chapelle -> Aachen)
    - If there are multiple entities, put the start entity first and then the target entity:
      - e.g. "Is Münster located northeast of Düsseldorf?" -> ["Düsseldorf", "Münster"]
      - e.g. "Does Bocholt lie western of Münster?" -> ["Münster", "Bocholt"]
        because the query must check from Münster whether Bocholt lies western of it
      - e.g. "Does Seelze lie within the district of Hannover?" -> ["Seelze", "Hannover"]
      - e.g. "Does the district Hannover contains the city Seelze?" -> ["Hannover", "Seelze"]
      - e.g. "Does Münster in Bayern lie northern of Augsburg?" -> ["Augsburg", "Münster", "Bayern"]
    - Do NOT include the type ("City", "AdministrativeCommunity", "District", "AdministrativeDistrict", "FederalState") of an entity into the list
  </constraints>
</spatial_entities>

<hierarchy>
<task>assign EVERY spatial entity to one of the following hierarchies:</task>
  <constraints>
    - allowed hierarchy values:
        - "City",
        - "AdministrativeCommunity",
        - "District",
        - "AdministrativeDistrict",
        - "FederalState"
        - "State"
    - Return one item for every entity in the question.
    - Explicit type in question overrides defaults.
    - Default hierarchy is City.
    - German keywords:
        - Stadt -> City
        - Verwaltungsgemeinde -> AdministrativeCommunity
        - Kreis -> District
        - Regierungsbezirk -> AdministrativeDistrict
        - Bundesland -> FederalState
        - Land/Bundesstaat -> State
    - The entity Germany has always "State" as hierarchy level
  </constraints>
</hierarchy>

<target_type>
  <task>Return the type of the target entity in the question.</task>
  <constraints>
    - Return one of the following types: 
        City < AdministrativeCommunity < District < AdministrativeDistrict < FederalState < State
    - The target type is what is asked for in the question
    - The default value is City, when no type is mentioned
  </constraints>
</target_type> 

<decision_question>
  <task> Determine whether the question is a decision_question. </task>
  <constraints>
    - Return True, when the user asks for a yes or no answer (e.g. "Does Münster lie northern of Selm?")
    - Else return False
  </constrains>
</decision_question>

Query: {query}

"""

class HierarchyItem(BaseModel):
    entity_name: str
    hierarchy: Literal[
        "City",
        "AdministrativeCommunity",
        "District",
        "AdministrativeDistrict",
        "FederalState",
        "State"
    ]

class ParameterExtraction(BaseModel):
    language: str = Field(description="language of the input question")
    spatial_relationship: str = Field(description="type of relationship of interest in the question")
    cardinal_direction: Optional[str] = Field(description="cardinal relationships in the input question")
    spatial_entities: List[str]  = Field(description="list of spatial entities in the input question")
    distance_constraint: Optional[float]  = Field(description="distance constraints mentioned in the input question")
    radius: Optional[bool] = Field(default=False, description="whether or not the question implies a radius constraint")
    distance_between: bool = Field(description="whether or not two entities are explicitly compared")
    hierarchy: List[HierarchyItem] = Field(default_factory=list, description="hierarchy assignment for the entities mentioned in the question")
    target_type: str = Field(description="the type of the target entity that is asked for in the question")
    decision_question: bool = Field(description="whether or not the question is a decision question")

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
    decision_question: bool
    route: str

    # OUTPUT
    cypher_query: str
    result: str
    reasoning: str

# Hierarchy
HIERARCHY = [
    "City",
    "AdministrativeCommunity",
    "District",
    "AdministrativeDistrict",
    "FederalState",
    "State"
]
HIERARCHY_SHORT = {
    "City": "C",
    "AdministrativeCommunity": "V",
    "District": "D",
    "AdministrativeDistrict": "A",
    "FederalState": "F",
    "State": "S"
}

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
    """Extracts a JSON object from an LLM response (which may be wrapped)."""
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
    prompt = f"""
        You are a JSON data extractor. Do NOT call any function. Do NOT use tools.
        Just return a plain JSON object describing the question/instruction parameters.

        {instructions.format(query=question)}

        Return a JSON object that follows exactly this JSON Schema:
        {json.dumps(ParameterExtraction.model_json_schema(), indent=2)}

        Now respond for: "{question}"
        Return ONLY the JSON object, nothing else:
    """

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
        "decision_question": False
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
            if "community" in func_name:
                defaults["target_type"] = "AdministrativeCommunity"
            elif "district" in func_name and "administrative" not in func_name:
                defaults["target_type"] = "District"
            elif "administrative" in func_name:
                defaults["target_type"] = "AdministrativeDistrict"
            elif "federal" or "states" in func_name:
                defaults["target_type"] = "FederalState"
            elif "city" in func_name or "cities" in func_name:
                defaults["target_type"] = "City"
            elif "state" in func_name and "federal" not in func_name:
                defaults["target_type"] = "State"
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

    if response.spatial_relationship == "None": # or neue funktion is in Germany? output yes or no (llm basiert)
        return {
            **state,
            "result": "Not valid",
            "route": "verbalize",
            "language": response.language
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
        "decision_question": response.decision_question,
        "route": "add_inheritance"
    }


# Inheritance
def add_inheritance(state):
    source = get_source_type(state)
    target = state.get("target_type", "City")
    hierarchy = state.get("hierarchy")
    
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
    if inheritance == "same" and len(hierarchy) == 2:
        s = HIERARCHY.index(hierarchy[0].hierarchy)
        t = HIERARCHY.index(hierarchy[1].hierarchy)

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
    MATCH (start:{source})
    WHERE toLower(start.Name) CONTAINS toLower("{name}")

    WITH start,
        CASE
            WHEN toLower(start.Name) = toLower("{name}") THEN 2
            WHEN toLower(start.Name) STARTS WITH toLower("{name}") THEN 1
            ELSE 0
        END AS score

    WITH start, score
    ORDER BY score DESC

    OPTIONAL MATCH (start)-[:hasFootprint]->(g:Geometry)

    OPTIONAL MATCH path =
        (start)-[:hasFootprint]->(:Geometry)
        -[:within*1..]->(:Geometry)
        <-[:hasFootprint]-(parent)

    WITH start, g, score,
        collect(DISTINCT {{
            id: parent.ID,
            name: parent.Name
        }}) AS target

    RETURN {{
        start: {{
            id: start.ID,
            name: start.Name,
            centroid: start.Centroid
        }},
        score: score,
        target: target
    }} AS result
    """
    return {**state, "cypher_query": query}

# Within
def build_within_same(state):
    # within_same does not exist, but the code sometimes goes there. To prevent this error, this function returns a Null query
    query = "RETURN null AS result LIMIT 0"
    return {**state, "cypher_query": query}

def build_within_super_class(state):
    source = get_source_type(state)
    target = state["target_type"]
    name = get_source_name(state)

    query = f"""
        MATCH p = (start:{source})
        -[]->
        (:Geometry)
        -[:within*]->
        (g:Geometry)    
        <-[:hasFootprint]-
        (:{target})
        WHERE toLower(start.Name) CONTAINS toLower('{name}')

        WITH start, p,
        CASE
            WHEN toLower(start.Name) = toLower('{name}') THEN 2
            WHEN toLower(start.Name) STARTS WITH toLower('{name}') THEN 1
            ELSE 0
        END AS score
        WITH start, score, p
        ORDER BY score DESC
    
        WITH start, score, nodes(p) AS ns

        UNWIND ns AS n
        MATCH (obj)-[:hasFootprint]->(n)
        WHERE NOT obj:Geometry

        WITH start, score, collect(DISTINCT {{
            id: obj.ID,
            name: obj.Name
        }}) AS targets

        RETURN {{
            start: {{
                id: start.ID,
                name: start.Name
            }},
            score: score,
            target: targets
        }} AS result
    """
    return {**state, "cypher_query": query}

def build_within_sub_class(state):
    source = get_source_type(state)
    target = state["target_type"]
    name = get_source_name(state)

    query = f"""
        MATCH (start:{source})
        -[:hasFootprint]->
        (sourceGeom:Geometry)
        WHERE toLower(start.Name) CONTAINS toLower('{name}')

        MATCH (target:{target})
        -[:hasFootprint]->
        (targetGeom:Geometry)

        MATCH (targetGeom)-[:within*]->(sourceGeom)

        WITH start, target,
        CASE
            WHEN toLower(start.Name) = toLower('{name}') THEN 2
            WHEN toLower(start.Name) STARTS WITH toLower('{name}') THEN 1
            ELSE 0
        END AS score

        WITH start, score, collect(DISTINCT {{
            id: target.ID,
            name: target.Name
        }}) AS targets

        RETURN {{
            start: {{
                id: start.ID,
                name: start.Name
            }},
            score: score,
            target: targets
        }} AS result
        """
    return {**state, "cypher_query": query}

# touches
def build_touches_query(state):
    source = get_source_type(state)
    name = get_source_name(state)

    # Filter for direction if specified
    direction = state.get("cardinal_direction")
    direction_filter = f"{{Rel_Position: '{direction}'}}" if direction else ""

    within_query = ""

    # Trying to determine whether the user asked for a higher level
    if len(state["spatial_entities"]) > 1 and state["decision_question"] == False:
        test_if_other_hierarchy = False
        for entity in state["hierarchy"]:
            if entity.hierarchy != source:
                test_if_other_hierarchy = True
                break
        if test_if_other_hierarchy:
            within_query = f"""
                MATCH (start)-[:hasFootprint]->(g:Geometry)

                MATCH path =
                    (start)-[:hasFootprint]->(:Geometry)
                    -[:within*1..]->(:Geometry)
                    <-[:hasFootprint]-(:{state["hierarchy"][1].hierarchy} {{Name: '{state["hierarchy"][1].entity_name}'}})
            """

    query = f"""
        MATCH 
        (start:{source})
        -[:hasFootprint]->(:Geometry)
        -[:touches {direction_filter}]->(:Geometry)
        <-[:hasFootprint]-(neighbor:{source})

        WHERE toLower(start.Name) CONTAINS toLower('{name}')

        WITH start, neighbor,
        CASE
            WHEN toLower(start.Name) = toLower('{name}') THEN 2
            WHEN toLower(start.Name) STARTS WITH toLower('{name}') THEN 1
            ELSE 0
        END AS score

        {within_query}

        WITH start, score, collect(DISTINCT {{
            id: neighbor.ID,
            name: neighbor.Name
        }}) AS target
        RETURN {{
            start: {{
                id: start.ID,
                name: start.Name
            }},
            score: score,
            target: target
            {", rel_position: '" + direction + "'" if direction else ""}
        }} AS result
        """

    return {
        **state,
        "cypher_query": query
    }

# relates
def select_relates_type(state):
    if state["distance_between"] == True:
        return "distance_between"
    
    if (state["radius"] == True or state["distance_constraint"] is not None) and state.get("cardinal_direction"):
        return "radius_and_direction"

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

    if state["decision_question"] == True:
        # Only use entities that are mentioned in the question
        e1 = state["spatial_entities"][0]
        e2 = state["spatial_entities"][1]

        # Find out whether the user asked for a higher hierarchy than the source entity
        # other_hierarchy = ""
        # for entity in state["hierarchy"]:
        #     if entity.hierarchy == state["target_type"]:
        #         other_hierarchy = f"""
        #             MATCH (start)-[:hasFootprint]->(g:Geometry)

        #             MATCH path =
        #                 (start)-[:hasFootprint]->(:Geometry)
        #                 -[:within*1..]->(:Geometry)
        #                 <-[:hasFootprint]-(:{entity.hierarchy} {{Name: '{entity.entity_name}'}})
        #         """
        #         break

        query = f"""
            MATCH
                (n1:{source}),
                (n2:{source})
            WHERE
                toLower(n1.Name) CONTAINS toLower("{e1}")
                AND toLower(n2.Name) CONTAINS toLower("{e2}")

            WITH
                n1,
                n2,
                CASE
                    WHEN toLower(n1.Name) = toLower("{e1}") THEN 2
                    WHEN toLower(n1.Name) STARTS WITH toLower("{e1}") THEN 1
                    ELSE 0
                END AS score1,
                CASE
                    WHEN toLower(n2.Name) = toLower("{e2}") THEN 2
                    WHEN toLower(n2.Name) STARTS WITH toLower("{e2}") THEN 1
                    ELSE 0
                END AS score2

            RETURN {{
                start: {{
                    id: n1.ID,
                    name: n1.Name,
                    score: score1,
                    centroid: n1.Centroid
                }},
                target: [{{
                    id: n2.ID,
                    name: n2.Name,
                    score: score2,
                    centroid: n2.Centroid
                }}]
            }} AS result
            ORDER BY score1 + score2 DESC
            """
    else:
        # First get the ID of the source entity
        query = f"""
        MATCH (start:{source})
        WHERE toLower(start.Name) CONTAINS toLower("{name}")

        WITH start,
            CASE
                WHEN toLower(start.Name) = toLower("{name}") THEN 2
                WHEN toLower(start.Name) STARTS WITH toLower("{name}") THEN 1
                ELSE 0
            END AS score

        WITH start, score
        ORDER BY score DESC

        OPTIONAL MATCH (start)-[:hasFootprint]->(g:Geometry)

        OPTIONAL MATCH path =
            (start)-[:hasFootprint]->(:Geometry)
            -[:within*1..]->(:Geometry)
            <-[:hasFootprint]-(parent)

        WITH start, g, score,
            collect(DISTINCT {{
                id: parent.ID,
                name: parent.Name
            }}) AS target

        RETURN {{
            start: {{
                id: start.ID,
                name: start.Name,
                centroid: start.Centroid
            }},
            score: score,
            target: target
        }} AS result
        """
    records = graph.query(query)
    if not records or len(records) == 0:
        return {**state, "cypher_query": "RETURN null AS result LIMIT 0"}
    
    # Run the prompt which chooses the best result if multiple candidates are returned
    if len(records) > 1:
        state["result"] = records
        state = resolve_entity(state)
        records = state["result"]

    if state["decision_question"] == True:
        # When it is a decision question, srf.calculate_cardinal_direction() does not need to be called
        # Compare only chosen entities
        compare_direction = srf.get_cardinal_direction(
            tuple(map(float, records[0]["result"]["start"]["centroid"][7:-1].split())), 
            tuple(map(float, records[0]["result"]["target"][0]["centroid"][7:-1].split()))
        )

        query = f"""
                MATCH (start:{source} {{ID: '{records[0]["result"]["start"]["id"]}'}})
                MATCH (target:{source} {{ID: '{records[0]["result"]["target"][0]["id"]}'}})

                RETURN {{
                    start: {{
                        id: start.ID,
                        name: start.Name
                    }},
                    target: [{{
                        id: target.ID,
                        name: target.Name
                    }}],
                    direction: '{compare_direction}'
                }} AS result
                """

    else:
        # Now calculate the cardinal direction query using the retrieved ID
        # If there are multiple candidates, choose the first one
        query = srf.calculate_cardinal_direction(
            records[0]["result"]["start"]["id"], 
            records[0]["result"]["start"]["name"], 
            state["target_type"], 
            direction
        )

    return {**state, "cypher_query": query}

def build_radius_query(state):
    distance = state["distance_constraint"]
    source = get_source_type(state)
    name = get_source_name(state)

    # First get the ID of the source entity
    get_id_query = f"""
        MATCH (start:{source})
        WHERE toLower(start.Name) CONTAINS toLower("{name}")

        WITH start,
            CASE
                WHEN toLower(start.Name) = toLower("{name}") THEN 2
                WHEN toLower(start.Name) STARTS WITH toLower("{name}") THEN 1
                ELSE 0
            END AS score

        WITH start, score
        ORDER BY score DESC

        OPTIONAL MATCH (start)-[:hasFootprint]->(g:Geometry)

        OPTIONAL MATCH path =
            (start)-[:hasFootprint]->(:Geometry)
            -[:within*1..]->(:Geometry)
            <-[:hasFootprint]-(parent)

        WITH start, g, score,
            collect(DISTINCT {{
                id: parent.ID,
                name: parent.Name
            }}) AS target

        RETURN {{
            start: {{
                id: start.ID,
                name: start.Name,
                centroid: start.Centroid
            }},
            score: score,
            target: target
        }} AS result
        """
    records = graph.query(get_id_query)
    if not records or len(records) == 0:
        return {**state, "cypher_query": "RETURN null AS result LIMIT 0"}

    # Run the prompt which chooses the best result if multiple candidates are returned
    if len(records) > 1:
        state["result"] = records
        state = resolve_entity(state)
        records = state["result"]
    
    # Now calculate the radius query using the retrieved ID
    query = srf.calculate_radius(
        records[0]["result"]["start"]["id"], 
        name, 
        state["target_type"], 
        distance
    )

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
            (n1:{source}),
            (n2:{source})
        WHERE
            toLower(n1.Name) CONTAINS toLower("{e1}")
            AND toLower(n2.Name) CONTAINS toLower("{e2}")

        WITH
            n1,
            n2,
            CASE
                WHEN toLower(n1.Name) = toLower("{e1}") THEN 2
                WHEN toLower(n1.Name) STARTS WITH toLower("{e1}") THEN 1
                ELSE 0
            END AS score1,
            CASE
                WHEN toLower(n2.Name) = toLower("{e2}") THEN 2
                WHEN toLower(n2.Name) STARTS WITH toLower("{e2}") THEN 1
                ELSE 0
            END AS score2

        OPTIONAL MATCH (n1)-[:hasFootprint]->(g1:Geometry)

        OPTIONAL MATCH path1 =
            (n1)-[:hasFootprint]->(:Geometry)
            -[:within*1..]->(:Geometry)
            <-[:hasFootprint]-(parent1)

        OPTIONAL MATCH (n2)-[:hasFootprint]->(g2:Geometry)

        OPTIONAL MATCH path2 =
            (n2)-[:hasFootprint]->(:Geometry)
            -[:within*1..]->(:Geometry)
            <-[:hasFootprint]-(parent2)

        WITH n1, n2, g1, g2, score1, score2,
            collect(DISTINCT {{
                id: parent1.ID,
                name: parent1.Name
            }}) AS target1,
            collect(DISTINCT {{
                id: parent2.ID,
                name: parent2.Name
            }}) AS target2

        RETURN [{{
            start: {{
                id: n1.ID,
                name: n1.Name,
                score: score1,
                centroid: n1.Centroid
            }},
            target: target1
            }},{{
            start: {{
                id: n2.ID,
                name: n2.Name,
                score: score2,
                centroid: n2.Centroid
            }},
            target: target2
        }}] AS result
        ORDER BY score1 + score2 DESC
        """
    return {**state, "cypher_query": query}

def build_radius_and_direction_query(state):
    distance = state["distance_constraint"]
    direction = state.get("cardinal_direction")
    source = get_source_type(state)
    name = get_source_name(state)

    # First get the ID of the source entity
    get_id_query = f"""
        MATCH (start:{source})
        WHERE toLower(start.Name) CONTAINS toLower("{name}")

        WITH start,
            CASE
                WHEN toLower(start.Name) = toLower("{name}") THEN 2
                WHEN toLower(start.Name) STARTS WITH toLower("{name}") THEN 1
                ELSE 0
            END AS score

        WITH start, score
        ORDER BY score DESC

        OPTIONAL MATCH (start)-[:hasFootprint]->(g:Geometry)

        OPTIONAL MATCH path =
            (start)-[:hasFootprint]->(:Geometry)
            -[:within*1..]->(:Geometry)
            <-[:hasFootprint]-(parent)

        WITH start, g, score,
            collect(DISTINCT {{
                id: parent.ID,
                name: parent.Name
            }}) AS target

        RETURN {{
            start: {{
                id: start.ID,
                name: start.Name,
                centroid: start.Centroid
            }},
            score: score,
            target: target
        }} AS result
        """
    records = graph.query(get_id_query)
    if not records or len(records) == 0:
        return {**state, "cypher_query": "RETURN null AS result LIMIT 0"}

    # Run the prompt which chooses the best result if multiple candidates are returned
    if len(records) > 1:
        state["result"] = records
        state = resolve_entity(state)
        records = state["result"]

    records = graph.query(get_id_query)
    if not records or len(records) == 0:
        return {**state, "cypher_query": "RETURN null AS result LIMIT 0"}
    
    # Now calculate the radius query using the retrieved ID
    query = srf.calculate_radius(
        records[0]["result"]["start"]["id"],
        name, 
        state["target_type"], 
        distance, 
        direction
    )

    return {**state, "cypher_query": query}

# execute query
def execute_query(state):
    global graph
    result = graph.query(state["cypher_query"])
    cleaned = [r["result"] for r in result]

    # When it is a decision question, only show the geometries mentioned in the question
    if state["decision_question"] == True:
        for r in cleaned:
            target = []
            for item in r["target"]:
                for entity in state["hierarchy"]:
                    if entity.entity_name in item["name"] and item["id"][0] == HIERARCHY_SHORT[entity.hierarchy]:
                        target.append(item)
            r["target"] = target
     
    return {**state, "result": cleaned}

# resolve entity
def resolve_entity(state):

    # If there is only one result or if its empty, return it directly
    if len(state["result"]) == 1 or len(state["result"]) == 0:
        return state
    
    # Printable JSON
    hierarchy = ", ".join(
        f"{item.entity_name} ({item.hierarchy})"
        for item in state["hierarchy"]
    )

    results = []
    for i, r in enumerate(state["result"]):
        item = r if isinstance(r, dict) else {"result": r}
        results.append({
            "index": i,
            **item
        })

    prompt = f"""
    You are a selection system for entity disambiguation.

    IMPORTANT:
    You do NOT perform semantic reasoning or guessing.
    You select the result based on the provided score and the context of the question.

    Each result has a "priority score":
    - score 2 = exact match
    - score 1 = match starts with the entity name
    - score 0 = match only contains entity name

    RULES:
    1. Prefer higher score values.
    2. If multiple entities have the same highest score, you may return multiple indices.
    3. Do NOT use substring reasoning or external knowledge.
    4. Do NOT assume that similar names are related.
    5. If the user limits the question to a specific hierarchy level, use the information provided in the targets to decide.
        e.g. "Where is Münster in Bayern located?" -> results where the target holds Bayern  

    Examples:
    - "Münster" is NOT "Neumünster"
    - Only choose entities explicitly matching the query or best scored candidates

    OUTPUT FORMAT:
    {{
        "reasoning": "Explain your reasoning for the selection in plain text",
        "indices": [0, 2]
    }}
    - Use the result list
    - Return a single index in a list if one best match exists
    - Return a list of indices if multiple candidates share the best score
    - Each result contains a field "index".
    - Do NOT count the list yourself.
    - Copy the value of the "index" field exactly as it appears.
    - Never infer or renumber indices.

    Question:
    {state["question"]}

    Spatial entities of question:
    {state["spatial_entities"]}

    Results (sorted by score descending):
    {results}

    Hierarchies:
    {hierarchy}
    """
    indices = llm.invoke(prompt).content
    res = json.loads(indices)
    # Only save the chosen results based on the indices returned by the LLM
    # Different handling depending on whether the result is a list or a single object
    if type(state["result"][0]) != list:
        state["result"] = [state["result"][i] for i in res["indices"]]
    else:
        result = []
        for i in res["indices"]:
            result.append({
                "start": state["result"][0][0]["start"],
                "target": [state["result"][0][1]["start"]]
            })
        state["result"] = result

    state["reasoning"] = res["reasoning"]

    # adds the distance to the result (only works with two entities)
    if state["distance_between"] == True:
        state["result"] = srf.calculate_distances(state["result"])

    return state


# answer
def verbalize(state):

    # Answer when the result is not valid
    if state["result"] == "Not valid":
        prompt = f"""
            The user provided a question that does not seem to be about the geometries of Germany. The question was: "{state['question']}"
        """
        if "language" in state:
            prompt += f"""
                Answer in this Language: {state['language']}
            """
        prompt += f"""
            Answer the following:
            Hello. This chatbot answers only questions about the geometries of Germany. Please try again with a different question.
        """
    else:

        # Regular answer
        prompt = f"""
        Turn the result into natural language based on the context of the question. 
        Do not use any external knowledge, only the information provided in the result.

        Question: {state['question']}
        Result: {state['result']}
        spatial_relationship: {state['spatial_relationship']}

        Answer in this Language: {state['language']}

        Describe all hierarchy levels of the result in the answer. 

        Hierarchy (lowest to highest):
        City < AdministrativeCommunity < District < AdministrativeDistrict < FederalState < State

        Important:
        - FederalState and State are two different hierarchy levels.
        - FederalState represents a German "Bundesland" (e.g. Hessen, Bayern, Nordrhein-Westfalen).
        - State represents the sovereign country. In this dataset there is exactly one State: Germany.
        - No other entity than Germany may ever be described as a State or Bundesstaat.
        - Hessen, Bayern, Sachsen, etc. are always FederalStates (Bundesländer), never States (Bundesstaaten).

        If language is German, use these translations:
        - City -> Stadt
        - AdministrativeCommunity -> Verwaltungsgemeinde
        - District -> Kreis
        - AdministrativeDistrict -> Regierungsbezirk
        - FederalState -> Bundesland
        - State -> Bundesstaat

        Examples:
        ✓ Frankfurt am Main liegt im Bundesland Hessen in Deutschland.
        ✓ Bayern ist ein Bundesland Deutschlands.
        ✓ Deutschland ist ein Bundesstaat.

        ✗ Frankfurt am Main liegt im Bundesstaat Hessen.
        ✗ Hessen ist ein Bundesstaat.
        ✗ Bayern ist ein Staat.

        Rules:
        - If the result includes distance (float), it is a distance in km.
        - The first letter of the id states the hierarchy level:
            - C = City
            - V = AdministrativeCommunity
            - D = District
            - A = AdministrativeDistrict
            - F = FederalState
            - S = State
        - Include the hierarchy level in the answer, but NEVER mention the id.
        - If {state['spatial_relationship']} == location: Include ALL hierarchy levels of the result in your answer!
        - The hierarchy must always end with Germany as the State.

        - If it is a decision-question:
            - Use the provided result to first answer with "yes" or "no"
            - Then say the reasoning for the answer based on the result
            Further information:
            - If the result is empty: the answer is no
            - Length of target: {len(state["result"][0]["target"]) if len(state["result"]) != 0 else 0}
                - If length of targets > 0 = True: the answer is yes, else the answer is no
            - rephrase the question as answer

        - If the result includes more than one startpoint:
            - The entity in question is not unique and refers to more than one place.
            - Always differentiate between the two results and always describe the location of both.

        - If the result is empty, answer:
            - Answer the question with the information, that nothing no geometry found.
        - The Result is never a question
        - Put only the result in the Answer NEVER the question
        - Do not use Markdown or code formatting in the answer, just plain text
        - Do not use the terms "start", "target", "result" in the answer
        """
    if state['result'] is None or state['result'] == "Not valid" or (isinstance(state['result'], list) and len(state['result']) == 0):
        return {
            **state,
            "result": {
                "verbalized": llm.invoke(prompt).content,
                "geometries": None
            }
        }
    
    # Convert to one array which holds all the entities
    flat = [
        {"id": obj["start"]["id"], "name": obj["start"]["name"]}
        for obj in state["result"]
    ] + [
        {"id": t["id"], "name": t["name"]}
        for obj in state["result"]
        for t in obj.get("target", [])
    ]

    return {
        **state,
        "result": {
            "verbalized": llm.invoke(prompt).content,
            "geometries": flat
        }
    }

# build graph
workflow = StateGraph(AgentState)

workflow.add_node("interpret_query", interpret_query)
workflow.add_node("add_inheritance", add_inheritance)

workflow.add_node("build_location_query", build_location_query)
workflow.add_node("build_within_same", build_within_same)
workflow.add_node("build_within_super_class", build_within_super_class)
workflow.add_node("build_within_sub_class", build_within_sub_class)
workflow.add_node("build_touches_query", build_touches_query)
workflow.add_node("add_relates_type", add_relates_type)

# relates
workflow.add_node("build_direction_query", build_direction_query)
workflow.add_node("build_radius_query", build_radius_query)
workflow.add_node("build_distance_between_query", build_distance_between_query)
workflow.add_node("build_radius_and_direction_query", build_radius_and_direction_query)

workflow.add_node("execute_query", execute_query)
workflow.add_node("resolve_entity", resolve_entity)
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
        "within_same": "build_within_same",
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
        "distance_between": "build_distance_between_query",
        "radius_and_direction": "build_radius_and_direction_query"
    }
)

workflow.add_edge("build_location_query", "execute_query")
workflow.add_edge("build_within_same", "execute_query")
workflow.add_edge("build_within_super_class", "execute_query")
workflow.add_edge("build_within_sub_class", "execute_query")
workflow.add_edge("build_touches_query", "execute_query")
workflow.add_edge("build_direction_query", "execute_query")
workflow.add_edge("build_radius_query", "execute_query")
workflow.add_edge("build_distance_between_query", "execute_query")
workflow.add_edge("build_radius_and_direction_query", "execute_query")

workflow.add_edge("execute_query", "resolve_entity")
workflow.add_edge("resolve_entity", "verbalize")
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
    # Format hierarchy to put it in a JSON
    i = 0
    if result.get("hierarchy"):
        for item in result["hierarchy"]:
            result["hierarchy"][i] = item.model_dump()
            i += 1
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
    example_question = "Where does Paris lie?"
    example_api_key = os.getenv("OPENAI_API_KEY")
    if example_api_key:
        result = run_question(example_question, example_api_key, "gpt-5.4-nano")

        fancy_print(result)
    else:
        print("Please set OPENAI_API_KEY before running the script directly.")