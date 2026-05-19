# Import und Setup
# Install
# pip install langgraph langchain langchain-openai neo4j

from typing import TypedDict, Literal, Optional, Dict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_community.graphs import Neo4jGraph

from rich.console import Console
from rich.panel import Panel
from rich.json import JSON

import os

from typing import List
from pydantic import BaseModel, Field

llm = None
graph = None


def build_chain(apiKey):
    global llm, graph
    os.environ["OPENAI_API_KEY"] = apiKey

    llm = ChatOpenAI(model="gpt-5.4-nano", temperature=0)
    graph = Neo4jGraph(
        url="neo4j://localhost:7687",
        username="neo4j",
        password="chatwithgermany"
    )

# Pydantic and llm_with_structured_output

relationship_description = """
Classify the question into one of these intents:
    - "within": hierarchical containment (lies in, belongs to, is in)
    - "touches": geographic neighbors (lies next to, is next to, touches)
    - "relates": generic relation, cardinal direction or distance (how far, north/south/east/west)
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
    - Extract ONLY if a distance constraint is mentioned
    - Convert all numbers to numeric values (no strings)
    - Normalize units:
    - "km", "kilometer" → km
    - "m", "meter" → m
"""

distance_between_description = """
    - TRUE only if TWO entities are explicitly compared
    - keywords: "between", "distance from X to Y", "What is the distance.."
"""

hierachy_assignment_description = """
    - Assign the entities to one of the following hierarchies:
    City < District < AdministrativeDistrict < FederalState

    - Return the answer as a list of strings of the format entity:hierarchy

    Rules:
    - If a Type ("City | AdministrativeDistrict | District | FederalState") is stated in the question like in the following examples:
        - If "administrative District of" or "the administrative District ..." is in the question → entity:AdministrativeDistrict
        - If "District of" or "the District ..." is in the question → entity:District
        - If "federal State of" or "the federal State ..." is in the question → entity:FederalStat

        - If asking "Which Cities lie within ..." → entity:"District" or entity:"AdministrativeDistrict" or entity:"FederalState"
        - If asking "Which Districts lie within ..." → entity:"AdministrativeDistrict" or entity:"FederalState"
        - If asking "Which administrative Districts lie within ..." → entity:"FederalState"

        - If asking "Which Cities lie next to (border) ..." → entity:"City"
        - If asking "Which administrative Districts lie next to (border) ..." → entity:"AdministrativeDistrict"
        - If asking "Which Districts lie next to (border) ..." → entity:"District"
        - If asking "Which federal States lie next to (border) ..." → "FederalState"
"""

spatial_entities_description = """
     List of entity names:
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
    cardinal_direction: str = Field(description=cardinal_direction_description)
    spatial_entities: List[str]  = Field(description=spatial_entities_description)
    distance_constraint: str  = Field(description=distance_constraint_description)
    distance_between: str = Field(description=distance_between_description)
    hierarchy: List[str] = Field(description=hierachy_assignment_description)
    target_type: str = Field(description=target_type_description)

class AgentState(TypedDict):
    # INPUT
    question: str

    language: str
    spatial_relationship: str
    cardinal_direction: str
    distance_between: bool
    spatial_entities: str
    distance_constraint: str
    hierarchy: str
    target_type: str

    # OUTPUT
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
    model = ChatOpenAI(model="gpt-5-mini", temperature=0)
    structured_llm = model.with_structured_output(schema=ParameterExtraction)
    response = structured_llm.invoke(question)
    return {
            **state,
            "language": response.language,
            "spatial_relationship": response.spatial_relationship,
            "cardinal_direction": response.cardinal_direction,
            "distance_between": response.distance_between,
            "spatial_entities": response.spatial_entities,
            "distance_constraint": response.distance_constraint,
            "hierarchy": response.hierarchy,
            "target_type": response.target_type
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
        (start:{state['source_type']} {{Name: '{state['entity_name']}'}})
        -[:hasFootprint]->(:Geometry)
        <-[:touches]-(:Geometry)
        <-[:hasFootprint]-(neighbor:{state['source_type']})

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
    if state.get("distance_between"):
        return "distance_between"

    if state.get("distance_filter"):
        return "distance_filter"

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
    (start:{state['source_type']} {{Name: '{state['entity_name']}'}})
    -[:hasFootprint]->(g1:Geometry)
    -[r:relates {rel_filter}]->(g2:Geometry)
    <-[:hasFootprint]-(other:{state['source_type']})

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

def build_distance_filter_query(state):
    distance = state.get("distance_filter")

    op = distance.get("operator")
    value = distance.get("value")

    query = f"""
    MATCH 
    (start:{state['source_type']} {{Name: '{state['entity_name']}'}})
    -[:hasFootprint]->(g1:Geometry)
    -[r:relates]->(g2:Geometry)
    <-[:hasFootprint]-(other:{state['source_type']})

    WHERE r.Distance_between {op} {value}

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
    e1 = state["entity_name"]
    e2 = state["second_entity"]

    query = f"""
    MATCH 
    (a:{state['source_type']} {{Name: '{e1}'}})
    -[:hasFootprint]->(g1:Geometry)
    -[r:relates]->(g2:Geometry)
    <-[:hasFootprint]-(b:{state['source_type']} {{Name: '{e2}'}})

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
    result = graph.query(state["cypher_query"])

    cleaned = [r["result"] for r in result]

    return {**state, "result": cleaned}

# answer
def verbalize(state):
    prompt = f"""
Turn into natural English:

Question: {state['question']}
Result: {state['result']}

Rules:
- If the result is a number, it is a Distance in m.
- The Result is never a question
- Put only the result in the Answer NEVER the question
"""

    return {
        **state,
        "result": llm.invoke(prompt).content
    }

# build graph
workflow = StateGraph(AgentState)

workflow.add_node("interpret_query", interpret_query)
workflow.add_node("add_direction", add_direction)

workflow.add_node("build_within_up", build_within_up)
workflow.add_node("build_within_down", build_within_down)
workflow.add_node("build_touches_query", build_touches_query)
workflow.add_node("add_relates_type", add_relates_type)

#relates
workflow.add_node("build_direction_query", build_direction_query)
workflow.add_node("build_distance_filter_query", build_distance_filter_query)
workflow.add_node("build_distance_between_query", build_distance_between_query)

workflow.add_node("execute_query", execute_query)
workflow.add_node("verbalize", verbalize)

workflow.add_edge(START, "interpret_query")
workflow.add_edge("interpret_query", "add_direction")

workflow.add_conditional_edges(
    "add_direction",
    select_query_type,
    {
        "within_up": "build_within_up",
        "within_down": "build_within_down",
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
        "distance_filter": "build_distance_filter_query",
        "distance_between": "build_distance_between_query"
    }
)

workflow.add_edge("build_within_up", "execute_query")
workflow.add_edge("build_within_down", "execute_query")
workflow.add_edge("build_touches_query", "execute_query")
workflow.add_edge("build_direction_query", "execute_query")
workflow.add_edge("build_distance_filter_query", "execute_query")
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
        f"[bold green]ANSWER[/bold green]\n{result.get('result')}",
        border_style="green"
    ))

    # Optional: komplette Rohdaten schön als JSON
    console.print("[bold yellow]FULL OUTPUT[/bold yellow]")
    console.print(JSON.from_data(result))

    console.print("\n" + "═"*80 + "\n")

def run_question(question: str, apiKey: str):
    """Initialisiert LLM und Neo4j und führt die Frage aus."""
    build_chain(apiKey)
    return compiled_graph.invoke({"question": question})


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
    example_question = "Which Cities lie in the administrative District of Münster?"
    example_api_key = ""
    if example_api_key:
        result = run_question(example_question, example_api_key)
        fancy_print(result)
    else:
        print("Bitte OPENAI_API_KEY setzen, bevor das Skript direkt ausgeführt wird.")