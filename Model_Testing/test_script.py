import json
import time
import requests
import pandas as pd
from langchain_openai import ChatOpenAI

# ============================================================
# Configuration
# ============================================================
INPUT_FILE = "Questions.xlsx"
OUTPUT_FILE = "test_results_gpt-5.4-nano.xlsx"

API_KEY = ""            # API key for the chat endpoint
API_KEY_JUDGE = ""      # API key for the judge (OpenAI)
CHAT_MODEL = "gpt-5.4-nano"
JUDGE_MODEL = "gpt-4o-mini"

QUESTION_COLUMN = "Question"
EXPECTED_COLUMN = "Expected_Answer"
LANGUAGE_COLUMN = "Language"
QUERY_TYPE_COLUMN = "Query_Type"

# ============================================================
# Judge initialization
# ============================================================
judge = ChatOpenAI(
    model=JUDGE_MODEL,
    api_key=API_KEY_JUDGE,
    temperature=0,
    model_kwargs={"response_format": {"type": "json_object"}},
)


# ============================================================
# Functions
# ============================================================
def chat(message: str, api_key: str, model: str) -> str:
    response = requests.post(
        "http://localhost:8000/api/chat",
        json={
            "message": message,
            "openAiKey": api_key,
            "selectedModel": model,
        },
        timeout=300,
    )
    response.raise_for_status()
    return response.json()["result"]["result"]["verbalized"]


def judge_answer(question: str, expected: str, actual: str):
    instructions = """
    Given an ACTUAL answer and an EXPECTED answer, determine whether
    the actual answer contains all of the information in the expected answer.
    When comparing geographic coordinates, accept ACTUAL answers within ±0.05° (approximately ±5 km) of the EXPECTED answer.
    If there is additional information in the ACTUAL answer, that's not a problem, as long as it is correct.

    Return ONLY valid JSON in this format:

    {
      "score": number between 0 and 1,
      "reason": "short explanation",
      "status": "PASSED" or "FAILED"
    }
"""
    user_message = f"""
QUESTION:
{question}

EXPECTED:
{expected}

ACTUAL:
{actual}
"""
    response = judge.invoke([
        {"role": "system", "content": instructions},
        {"role": "user", "content": user_message},
    ])

    try:
        parsed = json.loads(response.content.strip())
        return float(parsed["score"]), parsed["reason"], parsed["status"]
    except Exception as e:
        return 0.0, f"JSON parsing failed: {e}", "FAILED"


# ============================================================
# Main logic
# ============================================================
def main():
    print(f"Reading file: {INPUT_FILE}")
    df_in = pd.read_excel(INPUT_FILE)

    required_columns = [QUESTION_COLUMN, EXPECTED_COLUMN, LANGUAGE_COLUMN, QUERY_TYPE_COLUMN]
    missing = [c for c in required_columns if c not in df_in.columns]
    if missing:
        raise ValueError(f"The input file is missing the following columns: {missing}")

    # Build the result DataFrame with the columns to carry over
    df = pd.DataFrame({
        QUESTION_COLUMN: df_in[QUESTION_COLUMN],
        EXPECTED_COLUMN: df_in[EXPECTED_COLUMN],
        LANGUAGE_COLUMN: df_in[LANGUAGE_COLUMN],
        QUERY_TYPE_COLUMN: df_in[QUERY_TYPE_COLUMN],
    })

    # Create result columns
    df["Actual_Answer"] = ""
    df["Score"] = 0.0
    df["Status"] = ""
    df["Reason"] = ""
    df["Runtime (s)"] = 0.0

    total = len(df)
    for idx, row in df.iterrows():
        question = str(row[QUESTION_COLUMN]).strip()
        expected = str(row[EXPECTED_COLUMN]).strip()

        if not question or question.lower() == "nan":
            print(f"[{idx + 1}/{total}] Skipped (empty question)")
            continue

        print(f"[{idx + 1}/{total}] Question: {question[:80]}...")

        # 1) Get the answer from the chat API and measure runtime
        start_time = time.perf_counter()
        try:
            actual = chat(question, API_KEY, CHAT_MODEL)
            runtime = time.perf_counter() - start_time
        except Exception as e:
            runtime = time.perf_counter() - start_time
            actual = f"ERROR: {e}"
            print(f"   Chat API error: {e}")
            df.at[idx, "Actual_Answer"] = actual
            df.at[idx, "Score"] = 0.0
            df.at[idx, "Status"] = "ERROR"
            df.at[idx, "Reason"] = str(e)
            df.at[idx, "Runtime (s)"] = round(runtime, 3)
            continue

        # 2) Have the judge evaluate the answer
        try:
            score, reason, status = judge_answer(question, expected, actual)
        except Exception as e:
            score, reason, status = 0.0, f"Judge error: {e}", "ERROR"
            print(f"   Judge error: {e}")

        df.at[idx, "Actual_Answer"] = actual
        df.at[idx, "Score"] = score
        df.at[idx, "Status"] = status
        df.at[idx, "Reason"] = reason
        df.at[idx, "Runtime (s)"] = round(runtime, 3)

        print(f"   -> {status} (Score: {score}, Runtime: {runtime:.2f}s)")

        # Intermediate save after each row (prevents data loss on crash)
        df.to_excel(OUTPUT_FILE, index=False)

        # Small pause to avoid overloading the API
        time.sleep(0.5)

    # Final save
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"\nDone! Results saved to: {OUTPUT_FILE}")

    # Summary
    passed = (df["Status"] == "PASSED").sum()
    failed = (df["Status"] == "FAILED").sum()
    errors = (df["Status"] == "ERROR").sum()
    avg_score = df["Score"].mean()
    avg_runtime = df["Runtime (s)"].mean()
    total_runtime = df["Runtime (s)"].sum()

    print("\n=== Summary ===")
    print(f"PASSED:          {passed}")
    print(f"FAILED:          {failed}")
    print(f"ERRORS:          {errors}")
    print(f"Average score:   {avg_score:.2f}")
    print(f"Average runtime: {avg_runtime:.2f}s")
    print(f"Total runtime:   {total_runtime:.2f}s")


if __name__ == "__main__":
    main()