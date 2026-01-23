"""
auto_context.py

Automatische Erkennung von benötigten Context-Sets basierend auf Keywords im Prompt.
Hilft dabei, relevante Dokumentation zu finden ohne explizite @tags.
"""

from typing import List, Dict

# Keyword-Mapping für Context-Sets
CONTEXT_KEYWORDS: Dict[str, List[str]] = {
    "@juce": ["juce", "juce framework", "audio plugin"],
    "@dsp": ["dsp", "filter", "signal processing", "audio processing", "fft", "convolution"],
    "@vue": ["vue", "vue.js", "vuejs", "composition api", "options api"],
    "@angular": ["angular", "typescript", "rxjs", "angular material"],
    "@react": ["react", "jsx", "hooks", "component", "useState", "useEffect"],
    "@svelte": ["svelte", "sveltekit", "reactive"],
    "@html": ["html", "markup", "semantic html", "html5"],
    "@css": ["css", "styling", "flexbox", "grid", "scss", "sass"],
    "@js": ["javascript", "js", "ecmascript", "async", "promise"],
    "@cmake": ["cmake", "cmakelists", "build system"],
    "@clang": ["clang", "llvm", "compiler"],
    "@vscode": ["vscode", "visual studio code", "extension"],
    "@ninja": ["ninja", "build tool"],
    "@vst": ["vst", "vst3", "steinberg"],
    "@clap": ["clap", "free audio"],
    "@au": ["audio unit", "au", "apple audio"],
    "@aax": ["aax", "avid", "pro tools"],
    "@webview2": ["webview2", "edge webview", "embedded browser"],
}


def detect_contexts(prompt: str) -> List[str]:
    """
    Erkennt benötigte Context-Sets basierend auf Keywords im Prompt.
    
    Args:
        prompt: User-Prompt Text
        
    Returns:
        Liste von Context-Set Namen (mit @)
    """
    prompt_lower = prompt.lower()
    detected = []
    
    for context_set, keywords in CONTEXT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in prompt_lower:
                if context_set not in detected:
                    detected.append(context_set)
                break
    
    return detected


def suggest_contexts(prompt: str, threshold: int = 1) -> Dict[str, int]:
    """
    Schlägt Context-Sets vor und gibt Score zurück.
    
    Args:
        prompt: User-Prompt Text
        threshold: Minimale Anzahl Keyword-Treffer für Vorschlag
        
    Returns:
        Dict mapping Context-Set zu Score (Anzahl Keyword-Treffer)
    """
    prompt_lower = prompt.lower()
    scores = {}
    
    for context_set, keywords in CONTEXT_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in prompt_lower)
        if score >= threshold:
            scores[context_set] = score
    
    # Sortiere nach Score (höchster zuerst)
    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))


if __name__ == "__main__":
    # Test
    test_prompts = [
        "How do I create a VST3 plugin with JUCE?",
        "I need help with Vue.js composition API and CSS grid",
        "Build system with CMake and Ninja",
    ]
    
    for prompt in test_prompts:
        print(f"\nPrompt: {prompt}")
        contexts = detect_contexts(prompt)
        print(f"Detected contexts: {contexts}")
        
        suggestions = suggest_contexts(prompt)
        print(f"Suggestions with scores: {suggestions}")
