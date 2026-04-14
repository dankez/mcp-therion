# Therion MCP Server (Anonymný Mentor) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vytvoriť MCP server v Pythone, ktorý umožní bezpečnú analýzu Therion dát pomocou anonymizačných filtrov a lokálnej kompilácie.

**Architecture:** Python-based MCP server využívajúci `mcp` SDK. Obsahuje regex-based anonymizér pre `.th` a `.th2` súbory a subproces pre spúšťanie `therion` binárky.

**Tech Stack:** Python 3.12, `mcp` SDK, `pytest` pre testovanie, `therion` (systémová binárka).

---

### Task 1: Setup Prostredia

**Files:**
- Create: `requirements.txt`
- Create: `pyproject.toml`
- Create: `.gitignore`

- [ ] **Step 1: Vytvoriť requirements.txt**
```text
mcp>=1.0.0
pytest>=8.0.0
```

- [ ] **Step 2: Vytvoriť .gitignore**
```text
__pycache__/
venv/
*.pyc
studnica.json
```

- [ ] **Step 3: Nastaviť venv a nainštalovať závislosti**
Run: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`

- [ ] **Step 4: Commit**
```bash
git add requirements.txt pyproject.toml .gitignore
git commit -m "chore: initial setup and dependencies"
```

---

### Task 2: Implementácia Anonymizéra

**Files:**
- Create: `src/anonymizer.py`
- Test: `tests/test_anonymizer.py`

- [ ] **Step 1: Napísať test pre anonymizáciu .th súboru**
```python
import pytest
from src.anonymizer import anonymize_th

def test_anonymize_th_removes_sensitive_data():
    content = "survey test\ncs lat-long\nfix 1 48.0 19.0\ndata normal from to length\n1 2 150.5\nendp"
    anonymized = anonymize_th(content)
    assert "cs lat-long" not in anonymized
    assert "fix 1" not in anonymized
    assert "1 2 0" in anonymized # Hodnota nahradená nulou
```

- [ ] **Step 2: Implementovať anonymize_th funkciu**
```python
import re

def anonymize_th(content):
    # Odstránenie citlivých riadkov
    sensitive_patterns = [r'^cs\s+.*', r'^fix\s+.*', r'^explo\s+.*', r'^date\s+.*', r'^team\s+.*', r'^author\s+.*']
    lines = content.splitlines()
    filtered_lines = []
    
    in_data_normal = False
    for line in lines:
        if any(re.match(p, line.strip()) for p in sensitive_patterns):
            continue
        
        if "data normal" in line:
            in_data_normal = True
            filtered_lines.append(line)
            continue
            
        if in_data_normal and line.strip() and not line.strip().startswith('end'):
            # Nahradenie čísel nulami, zachovanie názvov staníc (prvé dve slová)
            parts = line.split()
            if len(parts) > 2:
                new_line = f"      {parts[0]}       {parts[1]}   " + " ".join(["0"] * (len(parts) - 2))
                filtered_lines.append(new_line)
                continue
        
        if line.strip().startswith('end'):
            in_data_normal = False
            
        filtered_lines.append(line)
        
    return "\n".join(filtered_lines)
```

- [ ] **Step 3: Spustiť testy**
Run: `pytest tests/test_anonymizer.py`

- [ ] **Step 4: Commit**
```bash
git add src/anonymizer.py tests/test_anonymizer.py
git commit -m "feat: implement basic th anonymizer"
```

---

### Task 3: MCP Server Core a list_projects

**Files:**
- Create: `src/server.py`

- [ ] **Step 1: Základná kostra MCP servera**
```python
from mcp.server.fastmcp import FastMCP
import os

mcp = FastMCP("Therion Mentor")
DATA_ROOT = "/home/dankez/Downloads/dropbox-spolu/"

@mcp.tool()
def list_therion_projects():
    """Zoznam adresárov s Therion projektmi."""
    projects = []
    for d in os.listdir(DATA_ROOT):
        full_path = os.path.join(DATA_ROOT, d)
        if os.path.isdir(full_path):
            projects.append(d)
    return projects

if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 2: Testovanie nástroja list_projects**
Run: `python3 src/server.py` (v samostatnom termináli) a overenie cez MCP inšpektor alebo priamo.

- [ ] **Step 3: Commit**
```bash
git add src/server.py
git commit -m "feat: initial mcp server with list_projects tool"
```

---

### Task 4: Implementácia read_anonymized_th a compile_therion

**Files:**
- Modify: `src/server.py`

- [ ] **Step 1: Pridať nástroj read_anonymized_th**
```python
@mcp.tool()
def read_anonymized_th(rel_path: str):
    """Prečíta a anonymizuje .th súbor."""
    full_path = os.path.join(DATA_ROOT, rel_path)
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    from src.anonymizer import anonymize_th
    return anonymize_th(content)
```

- [ ] **Step 2: Pridať nástroj compile_therion**
```python
import subprocess

@mcp.tool()
def compile_therion(rel_path: str):
    """Spustí kompiláciu Therion lokálne."""
    full_path = os.path.join(DATA_ROOT, rel_path)
    dir_path = os.path.dirname(full_path)
    file_name = os.path.basename(full_path)
    
    try:
        result = subprocess.run(
            ['therion', file_name],
            cwd=dir_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return "Kompilácia úspešná."
        else:
            return f"Chyba pri kompilácii:\n{result.stderr}"
    except Exception as e:
        return f"Interná chyba: {str(e)}"
```

- [ ] **Step 3: Commit**
```bash
git add src/server.py
git commit -m "feat: add read and compile tools to mcp server"
```

---

### Task 5: Studnica (Vedomostná báza)

**Files:**
- Modify: `src/server.py`
- Create: `studnica.json`

- [ ] **Step 1: Pridať nástroje pre Studnicu**
```python
import json

STUDNICA_PATH = "studnica.json"

@mcp.tool()
def search_studnica(query: str):
    """Vyhľadá triky v Studnici."""
    if not os.path.exists(STUDNICA_PATH): return "Studnica je prázdna."
    with open(STUDNICA_PATH, 'r') as f:
        data = json.load(f)
    results = [v for k, v in data.items() if query.lower() in k.lower() or query.lower() in v.lower()]
    return results if results else "Nenašli sa žiadne záznamy."

@mcp.tool()
def add_to_studnica(topic: str, trick: str):
    """Pridá nový trik do Studnice."""
    data = {}
    if os.path.exists(STUDNICA_PATH):
        with open(STUDNICA_PATH, 'r') as f:
            data = json.load(f)
    data[topic] = trick
    with open(STUDNICA_PATH, 'w') as f:
        json.dump(data, f, indent=4)
    return f"Téma '{topic}' bola pridaná do Studnice."
```

- [ ] **Step 2: Commit**
```bash
git add src/server.py
git commit -m "feat: implement Studnica (Knowledge Base) tools"
```

---

### Task 6: JPG Asistent (th2 skeleton)

**Files:**
- Modify: `src/server.py`

- [ ] **Step 1: Pridať nástroj generate_th2_skeleton**
```python
@mcp.tool()
def generate_th2_skeleton(description: str):
    """Vygeneruje logickú kostru .th2 súboru z popisu."""
    # Jednoduchá generácia na základe kľúčových slov
    lines = ["layout local", "  scale 1 100", "endlayout", ""]
    lines.append(f"# Logická kostra pre: {description}")
    lines.append("scrap scrap1 -projection plan")
    lines.append("  line wall")
    lines.append("    10 10")
    lines.append("    20 10")
    lines.append("    20 20")
    lines.append("    10 20")
    lines.append("    10 10")
    lines.append("  endline")
    lines.append("endscrap")
    return "\n".join(lines)
```

- [ ] **Step 2: Finálny commit a cleanup**
```bash
git add src/server.py
git commit -m "feat: add th2 skeleton generator"
```
