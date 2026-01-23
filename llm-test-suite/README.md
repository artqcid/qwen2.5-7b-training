# LLM Test Suite

Automated testing framework for LLM quality, context usage, and content evaluation.

## Structure

- `tests/test_smoke.py` - Basic smoke tests (auto-generated from web_context_sets.json)
- `tests/test_context.py` - Context usage tests (coming soon)
- `tests/test_quality.py` - Content quality tests (coming soon)
- `llm_client.py` - HTTP client for llama.cpp
- `test_config.yaml` - Central configuration

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Run all smoke tests
```bash
python -m pytest tests/test_smoke.py -v
```

### Run with parallel execution
```bash
python -m pytest tests/test_smoke.py -v -n auto
```

### Run specific context test
```bash
python -m pytest tests/test_smoke.py -v -k "@juce"
```

## Configuration

Edit `test_config.yaml` to:
- Change LLM endpoint
- Adjust test parameters (timeout, n_predict, temperature)
- Override keyword expectations per context
- Set minimum keyword hits for passing

## Dynamic Test Generation

Smoke tests are automatically generated from `../mcp-server-misc/web_context_sets.json`.
When you add a new @context, a smoke test is automatically created for it.

No manual test maintenance required!
