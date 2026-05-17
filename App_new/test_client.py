import requests

BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/chat"

# OpenAI-Key (oder besser als Umgebungsvariable setzen, das ist sicherer als hardcoden)
OPENAI_KEY = "meinKey"


def chat(message: str, api_key: str) -> str:
    response = requests.post(
        f"{BASE_URL}{ENDPOINT}",
        json={"message": message, "openAiKey": api_key},
        timeout=60
    )
    response.raise_for_status()
    data = response.json()

    return data.get("result", {}).get("result", "Got no answer.")


def main():
    print("=== ChatWithGermany Testing ===")
    print("Type 'exit' to exit the application.\n")

    while True:
        msg = input("You: ").strip()
        if msg.lower() in ("exit", "quit"):
            print("Bye!")
            break
        if not msg:
            continue

        try:
            result = chat(msg, OPENAI_KEY)
            print("\nResponse:")
            print(result)
            print("\n")
            # Fehler abfangen
        except requests.exceptions.HTTPError as e:
            print(f"HTTP-error: {e}")
            print("Server-Antwort:", e.response.text)
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")


if __name__ == "__main__":
    main()