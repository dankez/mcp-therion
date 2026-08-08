import requests
import re
import os
import gzip
import json

# HTML kód so zoznamom archívov (skrátená verzia pre regex)
base_url = "https://mailman.speleo.sk/pipermail/therion/"
os.makedirs("sources/mailing-list", exist_ok=True)
STUDNICA_PATH = "studnica.json"

def load_studnica():
    if os.path.exists(STUDNICA_PATH):
        try:
            with open(STUDNICA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_studnica(data):
    with open(STUDNICA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def add_to_studnica(data, topic, trick):
    data[topic] = trick

# Simulácia získania zoznamu (v reálnom prostredí by sme stiahli index.html)
# Tu použijem vzorku mesiacov a rokov, aby sme nezahltili systém, 
# ale skript je pripravený na kompletný zoznam.
years = range(2002, 2027)
months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

filenames = []
for y in years:
    for m in months:
        filenames.append(f"{y}-{m}.txt.gz")

print(f"Začínam sťahovanie a analýzu archívov...")

studnica_data = load_studnica()

for fname in filenames:
    url = base_url + fname
    # Skúsime stiahnuť len existujúce súbory
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            # Sanitizácia názvu súboru pre prevenciu Path Traversal
            safe_fname = os.path.basename(fname)
            file_path = f"sources/mailing-list/{safe_fname}"
            with open(file_path, "wb") as f:
                f.write(r.content)
            
            # Rozbalenie a analýza
            content = gzip.decompress(r.content).decode("utf-8", errors="ignore")
            txt_path = file_path.replace(".gz", "")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Hľadanie MetaPost kódov (def l_..., def p_..., def a_...)
            metapost_matches = re.findall(r"(def [lpa]_[a-z0-9_]+.*?enddef)", content, re.DOTALL | re.IGNORECASE)
            for i, match in enumerate(metapost_matches[:3]): # Len prvých pár unikátnych z každého mesiaca
                topic = f"MetaPost Hack ({fname} #{i+1})"
                # Skrátime na rozumnú dĺžku pre Studnicu
                snippet = match[:500] + ("..." if len(match) > 500 else "")
                add_to_studnica(studnica_data, topic, snippet)
            
            print(f"  [OK] {fname} - nájdené {len(metapost_matches)} trikov.")
    except Exception:
        pass # Súbor pravdepodobne neexistuje (budúcnosť alebo minulosť pred začiatkom listu)

save_studnica(studnica_data)

print("Proces dokončený.")
