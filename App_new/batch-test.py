import requests
from difflib import SequenceMatcher

BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/chat"
OPENAI_KEY = "meinKey"


# Test cases: (question, expected answer)
TEST_CASES = [
        {
        "question": "Where is the city of Coesfeld located?",
        "expected": "The city of Coesfeld is located in the district of Coesfeld, NRW, Germany.",
    },
    {
        "question": "Where is the district of Coesfeld located?",
        "expected": "The district of Coesfeld is located in the administrative district of Münster, NRW, Germany.",
    },
    {
        "question": "Where does the city of Coesfeld lie?",
        "expected": "The city of Coesfeld lies in the district of Coesfeld, NRW, Germany.",
    },
    {
        "question": "Where does the district of Coesfeld lie?",
        "expected": "The district of Coesfeld lies in the administrative district of Münster, NRW, Germany.",
    },
    {
        "question": "Where is the city of Coesfeld?",
        "expected": "The city of Coesfeld is in the district of Coesfeld, NRW, Germany.",
    },
    {
        "question": "Where is the district of Coesfeld?",
        "expected": "The district of Coesfeld is in the administrative district of Münster, NRW, Germany.",
    },

]


def chat(message: str, api_key: str) -> str:
    response = requests.post(
        f"{BASE_URL}{ENDPOINT}",
        json={"message": message, "openAiKey": api_key},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["result"]["result"]


def normalize(text: str) -> str:
    """Simplify text for comparison: convert to lowercase, normalize spaces."""
    return " ".join(text.lower().strip().split())


def similarity(a: str, b: str) -> float:
    """Returns a similarity score between 0 and 1."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def run_tests():
    results = []
    passed = 0
    failed = 0

    print(f"\n=== Starting {len(TEST_CASES)} Tests ===\n")

    for i, case in enumerate(TEST_CASES, 1):
        question = case["question"]
        expected = case["expected"]

        print(f"[{i}/{len(TEST_CASES)}] Question: {question}")

        try:
            actual = chat(question, OPENAI_KEY)
        except Exception as e:
            print(f"ERROR during API call: {e}\n")
            results.append({
                "question": question,
                "expected": expected,
                "actual": None,
                "status": "ERROR",
                "similarity": 0.0,
            })
            failed += 1
            continue

        sim = similarity(actual, expected)
        is_equal = normalize(actual) == normalize(expected)

        if is_equal or sim > 0.75:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1

        print(f"  Erwartet: {expected}")
        print(f"  Erhalten: {actual}")
        print(f"  {status} (Ähnlichkeit: {sim:.0%})\n")

        results.append({
            "question": question,
            "expected": expected,
            "actual": actual,
            "status": status,
            "similarity": round(sim, 3),
        })

    # Summary
    print("=" * 50)
    print(f"Test-results: {passed}/{len(TEST_CASES)} passed, {failed} failed")
    print("=" * 50)


if __name__ == "__main__":
    run_tests()