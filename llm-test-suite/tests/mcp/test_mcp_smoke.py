"""MCP smoke tests - dynamically generated from web_context_sets.json.

LLM smoke tests verify that the LLM has basic knowledge about each context.
Tests are automatically generated for each @context in web_context_sets.json.
"""
import pytest
import re
from typing import List


def extract_keywords_from_context(context_name: str, context_data: dict) -> List[str]:
    """Extract likely keywords from context name and URLs."""
    keywords = []
    
    # Context name (remove @)
    base_name = context_name.lstrip("@")
    keywords.append(base_name)
    
    # Common variations
    if base_name.lower() == "juce":
        keywords.extend(["AudioProcessor", "processBlock", "plugin"])
    elif base_name.lower() == "vue":
        keywords.extend(["Vue", "component", "reactive", "ref"])
    elif base_name.lower() == "react":
        keywords.extend(["React", "hooks", "useState", "component"])
    elif base_name.lower() == "angular":
        keywords.extend(["Angular", "component", "service", "module"])
    elif base_name.lower() == "dsp":
        keywords.extend(["signal", "frequency", "filter", "sample"])
    elif base_name.lower() == "vst":
        keywords.extend(["VST", "VST3", "plugin", "parameter"])
    elif base_name.lower() == "clap":
        keywords.extend(["CLAP", "plugin", "extension"])
    elif base_name.lower() == "cmake":
        keywords.extend(["CMake", "CMakeLists", "target", "add_"])
    
    return keywords


def generate_prompt_for_context(context_name: str) -> str:
    """Generate an appropriate test prompt for the context."""
    base_name = context_name.lstrip("@")
    
    prompts = {
        "juce": "What are the main methods in a JUCE AudioProcessor? List 3-5 key methods.",
        "vue": "What are the main features of Vue 3 Composition API? List 3-5 key functions.",
        "react": "What are React Hooks? List 3-5 common hooks.",
        "angular": "What are the main building blocks of Angular? List 3-5 core concepts.",
        "dsp": "What are common DSP operations? List 3-5 key concepts.",
        "vst": "What is VST3? Explain briefly in 2-3 sentences.",
        "clap": "What is CLAP audio plugin format? Explain briefly in 2-3 sentences.",
        "cmake": "What are common CMake commands? List 3-5 key functions.",
        "html": "What are common HTML5 elements? List 5 semantic tags.",
        "css": "What are common CSS layout methods? List 3-5 techniques.",
        "js": "What are key JavaScript ES6+ features? List 3-5 features.",
    }
    
    return prompts.get(base_name.lower(), f"What is {base_name}? Explain briefly.")


def pytest_generate_tests(metafunc):
    """Dynamically generate tests from web_context_sets.json."""
    if "context_name" in metafunc.fixturenames:
        # Load data directly (can't use fixtures here)
        import yaml
        import json
        from pathlib import Path
        
        # Load base config
        base_config_path = Path(__file__).parent.parent.parent / "test_config.yaml"
        with open(base_config_path) as f:
            test_config = yaml.safe_load(f)
        
        # Load MCP-specific smoke config
        mcp_config_path = Path(__file__).parent / "mcp_smoke_config.yaml"
        with open(mcp_config_path) as f:
            smoke_config = yaml.safe_load(f)
        
        # Get context file from base config
        context_file = base_config_path.parent / test_config["context_sets_file"]
        with open(context_file) as f:
            web_context_sets = json.load(f)
        
        # Generate test parameters
        test_params = []
        for context_name, context_data in web_context_sets.items():
            # Extract or override keywords
            if smoke_config.get("keyword_overrides", {}).get(context_name):
                keywords = smoke_config["keyword_overrides"][context_name]
            else:
                keywords = extract_keywords_from_context(context_name, context_data)
            
            # Generate prompt
            prompt = generate_prompt_for_context(context_name)
            
            test_params.append((context_name, prompt, keywords))
        
        # Parametrize the test
        metafunc.parametrize(
            "context_name,prompt,expected_keywords",
            test_params,
            ids=[name for name, _, _ in test_params]
        )


def test_context_smoke(
    context_name: str,
    prompt: str,
    expected_keywords: List[str],
    llm_client,
    smoke_config
):
    """Verify LLM has basic knowledge about the context.
    
    This test is auto-generated for each @context in web_context_sets.json.
    It sends a simple prompt and checks if the response contains expected keywords.
    """
    # Get response
    response = llm_client.get_content(prompt, n_predict=300)
    
    # Check keywords (case-insensitive)
    response_lower = response.lower()
    hits = 0
    matched_keywords = []
    
    for keyword in expected_keywords:
        # Use word boundary regex for better matching
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        if re.search(pattern, response_lower):
            hits += 1
            matched_keywords.append(keyword)
    
    min_hits = smoke_config.get("min_keyword_hits", 1)
    
    # Assertion with helpful message
    assert hits >= min_hits, (
        f"Context {context_name} smoke test failed!\n"
        f"Expected at least {min_hits} keywords from: {expected_keywords}\n"
        f"Found {hits}: {matched_keywords}\n"
        f"Response preview: {response[:200]}..."
    )
