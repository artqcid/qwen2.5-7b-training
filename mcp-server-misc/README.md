# Web Context MCP Server

Model Context Protocol (MCP) Server für automatisches Laden von Web-Dokumentation.

## Features

- **Context-Sets**: Vordefinierte Dokumentations-Sammlungen (@juce, @vue, @react, etc.)
- **Auto-Detection**: Automatische Erkennung benötigter Dokumentation basierend auf Keywords
- **Caching**: Intelligentes Caching von Web-Inhalten (24h)
- **Verschachtelung**: Support für verschachtelte Context-Sets (z.B. @frontend -> @vue, @react, ...)

## Installation

1. Python Virtual Environment erstellen:
```powershell
cd c:\mcp
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Dependencies installieren:
```powershell
pip install -r requirements.txt
```

3. MCP Server in VSCode registrieren (bereits in `User/mcp.json` konfiguriert):
```json
{
  "servers": {
    "web-context": {
      "type": "stdio",
      "command": "C:\\mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\mcp\\web_mcp.py"],
      "autoStart": true
    }
  }
}
```

## Verwendung

### Verfügbare Context-Sets

Siehe `web_context_sets.json` für alle verfügbaren Sets:

- **Framework**: `@juce`, `@vue`, `@react`, `@angular`, `@svelte`
- **Plugin-Formate**: `@vst`, `@clap`, `@au`, `@aax`
- **Tools**: `@cmake`, `@ninja`, `@clang`, `@vscode`
- **Web-Basics**: `@html`, `@css`, `@js`
- **Kombinationen**: `@frontend`, `@plugin`, `@toolset`, `@all`

### Auto-Detection

Die `auto_context.py` kann automatisch erkennen, welche Context-Sets basierend auf Keywords benötigt werden:

```python
from auto_context import detect_contexts, suggest_contexts

prompt = "How do I create a VST3 plugin with JUCE?"
contexts = detect_contexts(prompt)  # ['@juce', '@vst']

suggestions = suggest_contexts(prompt)  # {'@juce': 2, '@vst': 1}
```

## Dateien

- `web_mcp.py`: Haupt-MCP-Server
- `web_context_sets.json`: Konfiguration aller Context-Sets
- `auto_context.py`: Auto-Detection von benötigten Contexts
- `cache/`: Cache-Verzeichnis für Web-Inhalte
- `requirements.txt`: Python-Dependencies

## Troubleshooting

### Server startet nicht
```powershell
# Teste manuell:
cd c:\mcp
.venv\Scripts\Activate.ps1
python web_mcp.py
```

### Cache löschen
```powershell
Remove-Item -Recurse -Force c:\mcp\cache\*
```

### Dependencies aktualisieren
```powershell
pip install --upgrade -r requirements.txt
```
