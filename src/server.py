from mcp.server.fastmcp import FastMCP
import os
import subprocess
import json
from src.anonymizer import anonymize_th

mcp = FastMCP("Therion Mentor")
DATA_ROOT = "/home/dankez/Downloads/dropbox-spolu/"
STUDNICA_PATH = "studnica.json"

@mcp.tool()
def search_studnica(query: str):
    """Vyhľadá záznamy v Studnici (podľa kľúča alebo hodnoty)."""
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
    """Uloží novú tému a trik do Studnice."""
    data = {}
    if os.path.exists(STUDNICA_PATH):
        try:
            with open(STUDNICA_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            pass # Vytvoríme nový objekt, ak je súbor poškodený
            
    data[topic] = trick
    
    try:
        with open(STUDNICA_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return f"Téma '{topic}' bola úspešne pridaná do Studnice."
    except Exception as e:
        return f"Chyba pri ukladaní do Studnice: {str(e)}"

@mcp.tool()
def list_therion_projects():
    """Zoznam adresárov s Therion projektmi."""
    if not os.path.exists(DATA_ROOT):
        return f"Chyba: Adresár {DATA_ROOT} neexistuje."
    
    projects = []
    try:
        for d in os.listdir(DATA_ROOT):
            full_path = os.path.join(DATA_ROOT, d)
            if os.path.isdir(full_path):
                projects.append(d)
    except Exception as e:
        return f"Interná chyba pri prehľadávaní adresárov: {str(e)}"
        
    return projects

@mcp.tool()
def read_anonymized_th(rel_path: str):
    """Prečíta a anonymizuje .th súbor."""
    full_path = os.path.join(DATA_ROOT, rel_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return anonymize_th(content)
    except Exception as e:
        return f"Chyba pri čítaní súboru: {str(e)}"

@mcp.tool()
def compile_therion(rel_path: str):
    """Spustí kompiláciu Therion lokálne."""
    full_path = os.path.join(DATA_ROOT, rel_path)
    dir_path = os.path.dirname(full_path)
    file_name = os.path.basename(full_path)
    
    if not os.path.exists(full_path):
        return f"Chyba: Súbor {rel_path} neexistuje."
        
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

if __name__ == "__main__":
    mcp.run()
