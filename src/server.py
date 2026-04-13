from mcp.server.fastmcp import FastMCP
import os

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

if __name__ == "__main__":
    mcp.run()
