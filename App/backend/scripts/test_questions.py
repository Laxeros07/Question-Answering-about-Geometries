import os
import time
import pandas as pd

from agent_script import run_question

TEST_QUESTIONS = [
    # ------------------------------------------------------------------
    # A. Object / Footprint (Location)
    # ------------------------------------------------------------------
    {
        "query_type": "object/footprint",
        "question": "Where is the city of Münster located?"
    },
    {
        "query_type": "object/footprint",
        "question": "Where is the city of Cologne located?"
    },
    {
        "query_type": "object/footprint",
        "question": "Where is the administrative community of Eisenhüttenstadt located?"
    },
    {
        "query_type": "object/footprint",
        "question": "Where is the administrative community of Esens located?"
    },
    {
        "query_type": "object/footprint",
        "question": "Where is the district of Gießen located?"
    },
    {
        "query_type": "object/footprint",
        "question": "Where is the district of Nordsachsen located?"
    },
    {
        "query_type": "object/footprint",
        "question": "Where is the administrative district of Freiburg located?"
    },
    {
        "query_type": "object/footprint",
        "question": "Where is the administrative district of Oberfranken located?"
    },
    {
        "query_type": "object/footprint",
        "question": "Where is the federal state of Sachsen located?"
    },
    {
        "query_type": "object/footprint",
        "question": "Where is the federal state of Saarland located?"
    },

    # ------------------------------------------------------------------
    # B. Physical / Parts
    # ------------------------------------------------------------------
    {
        "query_type": "physical/parts",
        "question": "Which cities are part of the District of Coesfeld?"
    },
    {
        "query_type": "physical/parts",
        "question": "Which Districts are located within the Administrative District of Oberbayern?"
    },
    {
        "query_type": "physical/parts",
        "question": "Which Districts belong to the Federal State of Hessen?"
    },
    {
        "query_type": "physical/parts",
        "question": "Which administrative communities has the district of Steinburg?"
    },
    {
        "query_type": "physical/parts",
        "question": "How many cities belong to the district of Paderborn?"
    },

    # ------------------------------------------------------------------
    # Physical / Parts – Decision Questions
    # ------------------------------------------------------------------
    {
        "query_type": "physical/parts decision",
        "question": "Does the city of Dülmen lie within the District of Coesfeld?"
    },
    {
        "query_type": "physical/parts decision",
        "question": "Is the District of Coesfeld located in the Administrative District of Münster?"
    },
    {
        "query_type": "physical/parts decision",
        "question": "Does the Administrative District of Oberfranken belong to the Federal State of Bayern?"
    },
    {
        "query_type": "physical/parts decision",
        "question": "Is the District of Steinfurt located in the Federal State of Nordrhein-Westfalen?"
    },
    {
        "query_type": "physical/parts decision",
        "question": "Is the city of Bocholt located within the district of Cloppenburg?"
    },

    # ------------------------------------------------------------------
    # D. Object/spatial relationships (1:1)
    # Topological Relations (1:1)
    # ------------------------------------------------------------------
    {
        "query_type": "topological (1:1)",
        "question": "Do the Districts of Coesfeld and Borken touch each other?"
    },
    {
        "query_type": "topological (1:1)",
        "question": "Are the cities of Senden and Münster geographically disjoint?"
    },
    {
        "query_type": "topological (1:1)",
        "question": "Does the Federal State of Niedersachsen touch Nordrhein-Westfalen?"
    },
    {
        "query_type": "topological (1:1)",
        "question": "Is Berlin completely surrounded by Brandenburg?"
    },

    # Cardinal Direction Relations (1:1)
    # ------------------------------------------------------------------
    {
        "query_type": "cardinal (1:1)",
        "question": "Is Münster north of Dortmund?"
    },
    {
        "query_type": "cardinal (1:1)",
        "question": "Which city is located directly north of Jever?"
    },
    {
        "query_type": "cardinal (1:1)",
        "question": "Is Leipzig located eastern of Erfurt?"
    },

    # Distance Relations (1:1)
    # ------------------------------------------------------------------
    {
        "query_type": "distance (1:1)",
        "question": "What is the distance between the cities of Köln and Bonn?"
    },
    {
        "query_type": "distance (1:1)",
        "question": "How far is it from Hannover to Braunschweig?"
    },
    {
        "query_type": "distance (1:1)",
        "question": "How far are Hessen and Thüringen from each other?"
    },

    # ------------------------------------------------------------------
    # G. Object/spatial relationships (1:N)
    # Topological Relations (1:N)
    # ------------------------------------------------------------------
    {
        "query_type": "topological (1:N)",
        "question": "Which are the three closest districts to the district of Miesebach?"
    },
    {
        "query_type": "topological (1:N)",
        "question": "Which Districts touch the District of Warendorf?"
    },
    {
        "query_type": "topological (1:N)",
        "question": "Which administrative communities are adjacent to Leezen?"
    },
    {
        "query_type": "topological (1:N)",
        "question": "By which administrative districts is Mittelfranken surrounded?"
    },

    # Cardinal Direction Relations (1:N)
    # ------------------------------------------------------------------
    {
        "query_type": "cardinal (1:N)",
        "question": "Which Federal States are located north of Thüringen?"
    },
    {
        "query_type": "cardinal (1:N)",
        "question": "What Districts are west of Münster?"
    },
    {
        "query_type": "cardinal (1:N)",
        "question": "Which administrative communities are located north of the administrative community Morbach?"
    },

    # Distance Relations (1:N)
    # ------------------------------------------------------------------
    {
        "query_type": "distance (1:N)",
        "question": "Which Districts are located within a radius of 10 km from Göttingen?"
    },
    {
        "query_type": "distance (1:N)",
        "question": "Which cities are located in a radius of 15 km of Aachen?"
    },
    {
        "query_type": "distance (1:N)",
        "question": "Which cities are located less than 20 km around Munich?"
    },
]

MODELS = [
    "gpt-5.4-mini",
    #"gpt-5.4-nano"#,
    #"gpt-4o"
]

def benchmark():

    api_key = os.getenv("OPENAI_API_KEY")

    if api_key is None:
        raise RuntimeError("OPENAI_API_KEY not found.")

    rows = []

    total_runs = len(TEST_QUESTIONS) * len(MODELS)
    run = 1

    for model in MODELS:

        print("=" * 70)
        print(f"Testing model: {model}")
        print("=" * 70)

        for test in TEST_QUESTIONS:

            print(f"[{run}/{total_runs}] {test['question']}")

            start = time.perf_counter()

            try:

                result = run_question(
                    question=test["question"],
                    apiKey=api_key,
                    selectedModel=model
                )

                runtime = time.perf_counter() - start

                answer = result.get("result", {}).get("verbalized", "")

            except Exception as e:

                runtime = time.perf_counter() - start
                answer = f"ERROR: {e}"

            rows.append({
                "Model": model,
                "Query Type": test["query_type"],
                "Question": test["question"],
                "Answer": answer,
                "Runtime (s)": round(runtime, 3)
            })

            run += 1

    df = pd.DataFrame(rows)

    output_file = "qa_benchmark_results_mini.xlsx"

    df.to_excel(output_file, index=False)

    print()
    print("=" * 70)
    print(f"Finished. Results written to {output_file}")
    print("=" * 70)

if __name__ == "__main__":
    benchmark()