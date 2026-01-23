import requests
import re

def test_llama_cpp():
    url = "http://127.0.0.1:8080/v1/chat"
    headers = {"Content-Type": "application/json"}
    # Beispiel-Frage, die einen Link und Kontextbezug provozieren sollte
    data = {
        "model": "Qwen2.5-Coder-7B",
        "messages": [
            {"role": "user", "content": "Was ist ein Python Decorator? Bitte mit Link zur passenden Dokumentation."}
        ]
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code != 200:
        print(f"Fehler: {response.status_code}")
        print(response.text)
        return
    answer = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    print("Antwort vom LLM:")
    print(answer)
    # Prüfen, ob ein Link enthalten ist
    links = re.findall(r'https?://\S+', answer)
    if links:
        print("\n✅ Link(s) gefunden:")
        for link in links:
            print(link)
    else:
        print("\n❌ Kein Link in der Antwort gefunden!")

if __name__ == "__main__":
    test_llama_cpp()
