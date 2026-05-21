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

import os

from typing import List
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()  # Loads env variables from .env file

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
    - "location": the geographic position (Where lies, Where is located) 
    - "within": hierarchical containment (lies in, belongs to, is in)
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
    - Keywords: "within a radius of X km/m", "in a radius of X km/m", "within X km/m distance", "in X km/m distance"
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
    hierarchy: List[List[str]] = Field(description=hierarchy_assignment_description)
    target_type: str = Field(description=target_type_description)

class AgentState(TypedDict):
    # INPUT
    question: str
    apiKey: str
    selectedModel: str

    # Parameter
    language: str
    spatial_relationship: str
    cardinal_direction: str
    distance_between: bool
    spatial_entities: str
    distance_constraint: float
    radius: bool
    hierarchy: str
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
    
# Interpret Query
def interpret_query(state):
    question = state['question']
    api_key = state['apiKey']
    model_name = state['selectedModel']

    # initialize LLM
    global llm
    llm = ChatOpenAI(openai_api_key=api_key, model=model_name, temperature=0)
    model = ChatOpenAI(
        openai_api_key=api_key, 
        model=model_name, 
        temperature=1
    )
    llm = model

    structured_llm = model.with_structured_output(schema=ParameterExtraction)
    response = structured_llm.invoke(question)

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
    # Manually add City, when no hierarchy is given
    if len(state["hierarchy"]) == 0:
        state["hierarchy"] = [[state["spatial_entities"][0], "City"]]
    source = state["hierarchy"][0][1]
    target = state["target_type"]
    
    if source not in HIERARCHY or target not in HIERARCHY:
        inheritance = "sub_class"  # safe fallback
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

def build_location_query(state):
    source = state["hierarchy"][0][1]
    name = state["spatial_entities"][0]

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

    return {
        **state,
        "cypher_query": query
    }                                                                                                                                                                                                                                                                                                         

# Within
def build_within_super_class(state):
    source = state["hierarchy"][0][1]
    target = state["target_type"]
    name = state["spatial_entities"][0]

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
    source = state["hierarchy"][0][1]
    target = state["target_type"]
    name = state["spatial_entities"][0]

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
    return {
        **state,
        "cypher_query": f"""
        MATCH 
        (start:{state["hierarchy"][0][1]} {{Name: '{state["spatial_entities"][0]}'}})
        -[:hasFootprint]->(:Geometry)
        <-[:touches]-(:Geometry)
        <-[:hasFootprint]-(neighbor:{state["hierarchy"][0][1]})

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

    rel_filter = ""
    if direction:
        rel_filter = f"{{Spatial_relation: '{direction}'}}"

    query = f"""
    MATCH 
    (start:{state["hierarchy"][0][1]} {{Name: '{state["spatial_entities"][0]}'}})
    -[:hasFootprint]->(g1:Geometry)
    -[r:relates {rel_filter}]->(g2:Geometry)
    <-[:hasFootprint]-(other:{state["hierarchy"][0][1]})

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

    return {
        **state,
        "cypher_query": query
    }

def build_radius_query(state):
    distance = state["distance_constraint"]

    query = f"""
    MATCH 
    (start:{state["hierarchy"][0][1]} {{Name: '{state["spatial_entities"][0]}'}})
    -[:hasFootprint]->(g1:Geometry)
    -[r:relates]->(g2:Geometry)
    <-[:hasFootprint]-(other:{state["hierarchy"][0][1]})

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

    return {
        **state,
        "cypher_query": query
    }

# distance between
def build_distance_between_query(state):
    e1 = state["spatial_entities"][0]
    e2 = state["spatial_entities"][1]

    query = f"""
    MATCH 
    (a:{state["hierarchy"][0][1]} {{Name: '{e1}'}})
    -[:hasFootprint]->(g1:Geometry)
    -[r:relates]->(g2:Geometry)
    <-[:hasFootprint]-(b:{state["hierarchy"][0][1]} {{Name: '{e2}'}})

    WITH a,r, collect(DISTINCT {{
        id: b.ID,
        name: b.Name
    }}) AS target

    RETURN {{
        start: {{
            id: a.ID,
            name: a.Name
        }},
        target: target,
        distance: r.Distance_between
    }} AS result
    """

    return {
        **state,
        "cypher_query": query
    }

# execute query
def execute_query(state):
    global graph
    result = graph.query(state["cypher_query"])
    cleaned = [r["result"] for r in result]
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
    if state['result']==None:
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
            "start": state["result"][0]["start"],
            "target": state["result"][0]["target"],
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

#relates
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

# display graph
# pip install pillow
# pip install pygraphviz
#img_bytes = compiled_graph.get_graph().draw_mermaid_png()

#with open("graph.png", "wb") as f:
#    f.write(img_bytes)

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

    # Optional: komplette Rohdaten schön als JSON
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
    #questions = [
    #    "Which Cities lie in the administrative District of Münster?",
    #    "In which federal State lies Selm?",
    #    "What Cities lie in Rhein-Sieg-Kreis?",
    #    "Which administrative Districts lie next to Düsseldorf?",
    #    "Which City lie in a 10 km distance of Selm?",
    #    "What is the distance between Bocholt and Siegburg?",
    #    "Which Cities lie northern of Münster?"
    #]

    #for q in questions:
    #    result = compiled_graph.invoke({"question": q})
    #    fancy_print(result)
    example_question = "What lies 10km from Münster?"
    example_api_key = os.getenv("OPENAI_API_KEY")
    if example_api_key:
        result = run_question(example_question, example_api_key, "gpt-5-nano")
        fancy_print(result)
    else:
        print("Bitte OPENAI_API_KEY setzen, bevor das Skript direkt ausgeführt wird.")