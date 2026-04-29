import sys
from langchain_openai import ChatOpenAI
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain.prompts import PromptTemplate
import getpass
import os
import asyncio
import json
import re

from langchain.prompts.prompt import PromptTemplate

def create_chain(openAiKey):

    # Prompt for Cypher generation with few shot learning examples
    CYPHER_GENERATION_TEMPLATE = """
    Task:Generate Cypher statement to query a graph database and include the IDs of all the nodes which are used in the question and the answer as well as the asked properties from the user.
    Instructions:
    Never use the ID attribute in the answer sentence.
    Use only the provided relationship types and properties in the schema.
    Do not use any other relationship types or properties that are not provided.
    Use the unit km insteat of meters in your answer.
    All questions are in utf-8 encoded.
    Always return the whole graph (MATCH p=... RETURN p) in the Cypher statement.
    Do not use Markdown formatting. Do not use asterisks, bold text or italics. Return plain text only.
    Use the following examples for few shot learning.

    Schema:
    {schema}

    # In which District lies Siegburg?
    MATCH p=(:City {{Name: 'Siegburg'}}) - [:hasFootprint] -> (:Geometry) - [:within] -> (:Geometry) <- [:hasFootprint] - (:District) RETURN p

    # In which administrative District lies Rhein-Sieg-Kreis?
    MATCH p=(:District {{Name: "Rhein-Sieg-Kreis"}}) - [:hasFootprint] -> (:Geometry) - [:within] -> (:Geometry) <- [:hasFootprint] - (:AdministrativeDistrict) RETURN p

    # In which administrative District lies Siegburg?
    MATCH r1 =
    (:City {{Name: 'Siegburg'}})
        -[:hasFootprint]->(:Geometry)
        -[:within]->(:Geometry)
        <-[:hasFootprint]-(:District)

    MATCH r2 =
    (d)
        -[:hasFootprint]->(:Geometry)
        -[:within]->(:Geometry)
        <-[:hasFootprint]-(:AdministrativeDistrict)

    RETURN r1,r2

    # Which cities lie next to Siegburg?
    MATCH p=(:City {{Name: 'Siegburg'}}) - [:hasFootprint] -> (:Geometry) <- [:touches] - (:Geometry) <- [:hasFootprint] - (:City)  RETURN p

    Note: Do not include any explanations or apologies in your responses.
    Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
    Do not include any text except the generated Cypher statement.

    The question is:
    {question}"""
    CYPHER_GENERATION_PROMPT = PromptTemplate(
        input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
    )

    # Neo4j connection
    url = "neo4j://localhost:7687" #neo4j+ssc://f02e0524.databases.neo4j.io:7687"
    username = "neo4j"
    password = "chatwithgermany" #"w60PF-SK2gGIlDII6zZMw8XMo67mqIFSrPU54_E3AU4"

    graph = Neo4jGraph(
        url=url,
        username=username,
        password=password
    )

    # User Input for OpenAI API Key
    os.environ["OPENAI_API_KEY"] = openAiKey

    chain = GraphCypherQAChain.from_llm(
        graph=graph,
        cypher_llm=ChatOpenAI(temperature=0, model="gpt-5.4-nano"), # gpt-4o-mini	gpt-3.5-turbo
        qa_llm=ChatOpenAI(temperature=0, model="gpt-5.4-nano"),
        verbose=False,
        allow_dangerous_requests=True,
        cypher_prompt=CYPHER_GENERATION_PROMPT,
        return_intermediate_steps=True,
        top_k=9999
    )

    return chain

# Async function in Python - waits for the neo4j request before printing the answer
async def handle_request(chain,input_data):
    try:
        result = await chain.ainvoke(input_data)
        return result
    except Exception as e:
        return {
            "result": "An error occurred while processing the request.",
            "error": str(e),
            "type": type(e).__name__
        }

def run_query(question, openAiKey):
    chain = create_chain(openAiKey)

    # User Input for the question
    response = asyncio.run(handle_request(chain, question))

    json_response = json.dumps(response, indent=2)  # Convert to JSON format with indentation
    return(json_response)