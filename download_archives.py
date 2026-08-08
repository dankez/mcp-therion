import requests
import re
import os
import gzip

html = """
[Vložený HTML kód s odkazmi na .txt.gz]
""" # Použijem ten z vášho vstupu

# Extrahujeme názvy súborov
filenames = re.findall(r'href="([^"]+\.txt\.gz)"', html)
base_url = "https://mailman.speleo.sk/pipermail/therion/"
os.makedirs("sources/mailing-list", exist_ok=True)

print(f"Sťahujem {len(filenames)} súborov...")

for fname in filenames:
    # Sanitizácia názvu súboru pre prevenciu Path Traversal
    safe_fname = os.path.basename(fname)
    url = base_url + fname
    print(f"  -> {fname} (ukladám ako {safe_fname})")
    try:
        r = requests.get(url)
        with open(f"sources/mailing-list/{safe_fname}", "wb") as f:
            f.write(r.content)
            
        # Skúsime vybrať pár zaujímavých riadkov (prvých 10 KB z každého archívu)
        # pre Studnicu (len ak sú tam 'metapost' alebo 'fix')
        content = gzip.decompress(r.content).decode('utf-8', errors='ignore')
        if "metapost" in content.lower() or "hack" in content.lower():
            # TODO: Extrahovať konkrétny text a pridať do studnica.json
            pass
    except Exception as e:
        print(f"    CHYBA: {e}")

print("Hotovo.")
