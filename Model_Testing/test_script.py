import json
import time
import requests
import pandas as pd
import os
from langchain_openai import ChatOpenAI
from pathlib import Path
from dotenv import load_dotenv
from bert_score import score as bert_score

# ============================================================
# Configuration
# ============================================================
INPUT_FILE = "Questions.xlsx"
OUTPUT_FILE = "test_results_gpt-4o-mini.xlsx"

# load Keys from .env
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent / "App" / "backend" / ".env"
load_dotenv(dotenv_path=ENV_PATH)

API_KEY = os.getenv("OPENAI_API_KEY")  #OPENAI_API_KEY  or  SAIA_KEY
API_KEY_JUDGE = os.getenv("OPENAI_API_KEY")

# Fail fast if the keys are missing
if not API_KEY:
    raise EnvironmentError("API_KEY is not set. Please define it in your .env file.")
if not API_KEY_JUDGE:
    raise EnvironmentError("API_KEY_JUDGE is not set. Please define it in your .env file.")

CHAT_MODEL = "gpt-4o-mini"
JUDGE_MODEL = "gpt-5.4-nano"

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
def chat(message: str, api_key: str, model: str,
         max_retries: int = 3, backoff: float = 2.0) -> str:
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
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

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            last_error = e
            # Only retry on server errors (5xx) or 429 (rate limit)
            if status is not None and (500 <= status < 600 or status == 429):
                wait = backoff ** attempt
                print(f"   HTTP {status} received. Retry {attempt}/{max_retries} in {wait:.1f}s...")
                time.sleep(wait)
                continue
            raise
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout) as e:
            last_error = e
            wait = backoff ** attempt
            print(f"   Connection issue: {e}. Retry {attempt}/{max_retries} in {wait:.1f}s...")
            time.sleep(wait)

    # All retries exhausted
    raise last_error


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


def compute_bert_scores(actuals: list[str], expecteds: list[str]):
    """Compute BERTScore Precision, Recall and F1 for a list of answer pairs."""
    print("\nComputing BERTScore (this may take a moment)...")
    P, R, F1 = bert_score(
        actuals,
        expecteds,
        lang="en",
        model_type="bert-base-multilingual-cased",
        rescale_with_baseline=True,
        verbose=True,
    )
    return P.tolist(), R.tolist(), F1.tolist()

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
        LANGUAGE_COLUMN: df_in[LANGUAGE_COLUMN],
        QUERY_TYPE_COLUMN: df_in[QUERY_TYPE_COLUMN],
        QUESTION_COLUMN: df_in[QUESTION_COLUMN],
        EXPECTED_COLUMN: df_in[EXPECTED_COLUMN],
    })

    # Create result columns
    df["Actual_Answer"] = ""
    df["Runtime (s)"] = 0.0
    df["Score"] = 0.0
    df["Status"] = ""
    df["Reason"] = ""
    df["BERT_P"] = 0.0
    df["BERT_R"] = 0.0
    df["BERT_F1"] = 0.0

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
        time.sleep(10)


    # BERTScore

    # Only score rows where we have a valid actual answer
    valid_mask = (df["Status"] != "ERROR") & (df["Actual_Answer"].astype(str).str.len() > 0)
    valid_idx = df.index[valid_mask].tolist()

    if valid_idx:
        actuals = [str(df.at[i, "Actual_Answer"]) for i in valid_idx]
        expecteds = [str(df.at[i, EXPECTED_COLUMN]) for i in valid_idx]

        try:
            P_list, R_list, F1_list = compute_bert_scores(actuals, expecteds)
            for i, p, r, f1 in zip(valid_idx, P_list, R_list, F1_list):
                df.at[i, "BERT_P"] = round(float(p), 4)
                df.at[i, "BERT_R"] = round(float(r), 4)
                df.at[i, "BERT_F1"] = round(float(f1), 4)
        except Exception as e:
            print(f"BERTScore computation failed: {e}")

    
    # Append summary row with averages

    # Compute averages ignoring ERROR rows for the score/BERT metrics
    score_mask = df["Status"].isin(["PASSED", "FAILED"])

    avg_score = df.loc[score_mask, "Score"].mean() if score_mask.any() else 0.0
    avg_runtime = df["Runtime (s)"].mean()
    avg_p = df.loc[score_mask, "BERT_P"].mean() if score_mask.any() else 0.0
    avg_r = df.loc[score_mask, "BERT_R"].mean() if score_mask.any() else 0.0
    avg_f1 = df.loc[score_mask, "BERT_F1"].mean() if score_mask.any() else 0.0

    summary_row = {
        QUESTION_COLUMN: "AVERAGE",
        EXPECTED_COLUMN: "",
        LANGUAGE_COLUMN: "",
        QUERY_TYPE_COLUMN: "",
        "Actual_Answer": "",
        "Score": round(float(avg_score), 4),
        "Status": "",
        "Reason": "",
        "Runtime (s)": round(float(avg_runtime), 3),
        "BERT_P": round(float(avg_p), 4),
        "BERT_R": round(float(avg_r), 4),
        "BERT_F1": round(float(avg_f1), 4),
    }
    df = pd.concat([df, pd.DataFrame([summary_row])], ignore_index=True)

    # Final save
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"\nDone! Results saved to: {OUTPUT_FILE}")

    
    # Console summary
    passed = (df["Status"] == "PASSED").sum()
    failed = (df["Status"] == "FAILED").sum()
    errors = (df["Status"] == "ERROR").sum()
    total_runtime = df["Runtime (s)"].sum()

    print("\n=== Summary ===")
    print(f"PASSED:            {passed}")
    print(f"FAILED:            {failed}")
    print(f"ERRORS:            {errors}")
    print(f"Average score:     {avg_score:.4f}")
    print(f"Average BERT P:    {avg_p:.4f}")
    print(f"Average BERT R:    {avg_r:.4f}")
    print(f"Average BERT F1:   {avg_f1:.4f}")
    print(f"Average runtime:   {avg_runtime:.2f}s")
    print(f"Total runtime:     {total_runtime:.2f}s")


if __name__ == "__main__":
    main()