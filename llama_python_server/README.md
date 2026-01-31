# Llama.cpp Dynamic Model Server

Dieser Server lädt dynamisch Modelle basierend auf dem "model" Parameter in /v1/completions Requests.

- "qwen": Qwen2.5-Coder-7B (für Agent)
- "mistral": Mistral-7B-Instruct (für Chat/Plan)

Das Modell wird gewechselt, indem das alte entladen und das neue geladen wird (ohne Restart).

## Installation

pip install -r requirements.txt

## Start

python main.py

Läuft auf http://127.0.0.1:8080

## Integration

In Continue config.yaml die Modelle mit "model: qwen" und "model: mistral" definieren.