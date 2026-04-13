from mcp.server.fastmcp import FastMCP
import os
import subprocess
from src.anonymizer import anonymize_th

mcp = FastMCP("Therion Mentor")
DATA_ROOT = "/home/dankez/Downloads/dropbox-spolu/"

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
