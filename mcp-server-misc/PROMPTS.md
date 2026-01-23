# MCP Server - Verfügbare Prompt Templates

Diese Prompt-Templates sind über den MCP-Server in Continue/Cline verfügbar.

## 📁 Konfiguration

Die Prompts werden aus [prompts.json](prompts.json) geladen. Du kannst neue Prompts hinzufügen, indem du die JSON-Datei bearbeitest - kein Python-Code nötig!

### Struktur eines Prompts:

```json
{
  "name": "prompt_name",
  "description": "Beschreibung des Prompts",
  "arguments": [
    {
      "name": "parameter_name",
      "description": "Parameter-Beschreibung",
      "required": true
    }
  ]
}
```

---

## 🎵 Audio Plugin Development

### `juce_component`
**Beschreibung:** Erkläre JUCE-Komponente mit vollständiger Dokumentation

**Parameter:**
- `component_name` (required): Name der JUCE-Komponente (z.B. AudioProcessor, AudioParameterFloat)

**Beispiel-Verwendung:**
```
Prompt: juce_component
component_name: AudioProcessor
```

---

### `plugin_format`
**Beschreibung:** Erkläre Audio-Plugin-Format (VST3, CLAP, AU, AAX) mit Beispielen

**Parameter:**
- `format` (required): Plugin-Format: vst, clap, au, oder aax

**Beispiel-Verwendung:**
```
Prompt: plugin_format
format: vst
```

---

### `dsp_algorithm`
**Beschreibung:** Erkläre DSP-Algorithmus mit mathematischer Grundlage

**Parameter:**
- `algorithm` (required): DSP-Algorithmus (z.B. Biquad Filter, FFT, Delay)

**Beispiel-Verwendung:**
```
Prompt: dsp_algorithm
algorithm: Biquad Filter
```

---

## 🌐 Frontend Development

### `frontend_pattern`
**Beschreibung:** Erkläre Frontend-Pattern mit Framework-spezifischen Beispielen

**Parameter:**
- `pattern` (required): Design Pattern (z.B. Component Composition, State Management)
- `framework` (optional): Framework: vue, react, angular, oder svelte

**Beispiel-Verwendung:**
```
Prompt: frontend_pattern
pattern: State Management
framework: vue
```

---

## 🔧 Build & Tooling

### `cmake_setup`
**Beschreibung:** Erstelle CMake-Konfiguration für Projekt-Typ

**Parameter:**
- `project_type` (required): Projekt-Typ (z.B. JUCE Plugin, C++ Library, Header-only)

**Beispiel-Verwendung:**
```
Prompt: cmake_setup
project_type: JUCE Plugin
```

---

## ⚡ Quick Context Loading

Diese Prompts laden automatisch die relevanten Context-Sets.

### `load_audio_context`
**Beschreibung:** Lädt kompletten Audio-Development-Context (@audio mit JUCE, DSP, VST, CLAP)

**Parameter:** Keine

**Lädt:**
- @juce - JUCE Framework Dokumentation
- @dsp - Digital Signal Processing
- @vst - VST3 SDK
- @clap - CLAP Plugin Format
- @plugin - Alle Plugin-Formate

---

### `load_frontend_context`
**Beschreibung:** Lädt kompletten Frontend-Development-Context (@frontend mit Vue, React, etc.)

**Parameter:** Keine

**Lädt:**
- @vue - Vue.js
- @react - React
- @angular - Angular
- @svelte - Svelte
- @html - HTML
- @css - CSS
- @js - JavaScript

---

### `load_plugin_context`
**Beschreibung:** Lädt Plugin-Format-Context (@plugin mit VST, CLAP, AU, AAX)

**Parameter:** Keine

**Lädt:**
- @juce - JUCE Framework
- @vst - VST3
- @clap - CLAP
- @au - Audio Units
- @aax - AAX

---

## 🐛 Debugging & Best Practices

### `debug_issue`
**Beschreibung:** Debug-Hilfe mit relevanter Dokumentation

**Parameter:**
- `technology` (required): Technologie/Framework (z.B. juce, vue, cmake)
- `issue_description` (required): Kurze Beschreibung des Problems

**Beispiel-Verwendung:**
```
Prompt: debug_issue
technology: juce
issue_description: AudioProcessor crashes on buffer resize
```

---

### `best_practices`
**Beschreibung:** Best Practices für spezifische Technologie laden

**Parameter:**
- `technology` (required): Technologie (z.B. juce, react, cmake, dsp)

**Beispiel-Verwendung:**
```
Prompt: best_practices
technology: dsp
```

---

## 📋 Verwendung in Continue/Cline

1. **In Continue:** Die Prompts erscheinen in der Command Palette
2. **Aufruf:** `/prompt <name>` oder über das Prompt-Menü
3. **Parameter:** Continue fragt nach den erforderlichen Parametern

## 🔄 Automatische Context-Ladung

Die Prompts können automatisch die relevanten Context-Sets laden:
- `load_*_context` Prompts → Laden vordefinierte Context-Kombinationen
- Andere Prompts → Können bei Bedarf Context-Sets im Hintergrund aktivieren

## 🎯 Best Practices

1. **Spezifische Prompts** für gezielte Fragen (z.B. `juce_component`)
2. **Context-Loading Prompts** am Anfang einer Session
3. **Debug-Prompts** mit konkreter Problembeschreibung
4. **Kombination möglich:** Context laden + spezifische Frage

## 🚀 Erweiterung

Neue Prompts können direkt in [prompts.json](prompts.json) hinzugefügt werden - ohne Python-Code zu schreiben!

**JSON-Format:**
```json
{
  "name": "neuer_prompt",
  "description": "Was der Prompt macht",
  "arguments": [
    {
      "name": "parameter_name",
      "description": "Was dieser Parameter bedeutet",
      "required": true
    }
  ]
}
```

**Vorteile:**
- ✅ Keine Code-Änderungen nötig
- ✅ Einfach zu bearbeiten
- ✅ Automatisch geladen beim Server-Start
- ✅ Validierung durch JSON-Schema

**Nach Änderungen:** Server neu starten oder Continue neu laden.
