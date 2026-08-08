from mcp.server.fastmcp import FastMCP
import os
import subprocess
import json
from src.anonymizer import anonymize_th

mcp = FastMCP("Therion Mentor")
DATA_ROOT = "/home/dankez/Downloads/dropbox-spolu/"
STUDNICA_PATH = "studnica.json"
SOURCES_DIR = "sources"

# Vytvorenie adresára pre zdroje, ak neexistuje
if not os.path.exists(SOURCES_DIR):
    os.makedirs(SOURCES_DIR)

@mcp.tool()
def search_studnica(query: str):
    """Vyhľadá záznamy v Studnici (vaša vedomostná báza)."""
    if not os.path.exists(STUDNICA_PATH):
        return "Studnica je prázdna."
    
    try:
        with open(STUDNICA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        results = {}
        query_lower = query.lower()
        for k, v in data.items():
            if query_lower in k.lower() or query_lower in v.lower():
                results[k] = v
                
        if not results:
            return f"Nenašli sa žiadne záznamy pre dopyt: '{query}'."
        return results
    except Exception as e:
        return f"Chyba pri čítaní Studnice: {str(e)}"

@mcp.tool()
def add_to_studnica(topic: str, trick: str):
    """Pridá nový trik alebo poznatok do Studnice."""
    data = {}
    if os.path.exists(STUDNICA_PATH):
        try:
            with open(STUDNICA_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            pass
            
    data[topic] = trick
    
    try:
        with open(STUDNICA_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return f"Téma '{topic}' pridaná do Studnice."
    except Exception as e:
        return f"Chyba pri ukladaní: {str(e)}"

@mcp.tool()
def read_therion_file(rel_path: str, anonymize: bool = False):
    """
    Načíta Therion súbor (.th, .th2, .thcfg, .txt, thconfig).
    Predvolene načítava plnohodnotné dáta. Ak anonymize=True, citlivé údaje sa odfiltrujú.
    """
    full_path = os.path.join(DATA_ROOT, rel_path)
    
    if not os.path.exists(full_path):
        return f"Chyba: Súbor {rel_path} nebol nájdený."

    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if anonymize:
            return anonymize_th(content)
        return content
    except Exception as e:
        return f"Chyba pri čítaní súboru: {str(e)}"

@mcp.tool()
def list_therion_projects():
    """Zoznam projektov v dátovom úložisku."""
    if not os.path.exists(DATA_ROOT):
        return f"Chyba: {DATA_ROOT} neexistuje."
    return [d for d in os.listdir(DATA_ROOT) if os.path.isdir(os.path.join(DATA_ROOT, d))]

@mcp.tool()
def compile_therion(rel_path: str):
    """Spustí kompiláciu Therion lokálne a vráti výsledok."""
    full_path = os.path.join(DATA_ROOT, rel_path)
    dir_path = os.path.dirname(full_path)
    file_name = os.path.basename(full_path)
    
    try:
        result = subprocess.run(
            ['therion', file_name],
            cwd=dir_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return "Kompilácia úspešná."
        return f"Chyba pri kompilácii:\n{result.stderr}"
    except Exception as e:
        return f"Interná chyba: {str(e)}"

@mcp.tool()
def generate_th2_skeleton(description: str):
    """Vygeneruje logickú kostru .th2 súboru."""
    return f"layout local\n  scale 1 100\nendlayout\n\n# Kostra: {description}\nscrap scrap1 -projection plan\n  line wall\n    10 10\n    20 10\n    20 20\n    10 20\n    10 10\n  endline\nendscrap"

if __name__ == "__main__":
    mcp.run()
