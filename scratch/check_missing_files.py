import os
import re

DATA_ROOT = "/home/dankez/Downloads/dropbox-spolu/"
MAX_ERRORS = 20
IGNORE_DIRS = ['trash', 'tmp', 'old', 'zaloha'] # Pridal som aj zalohu pre istotu
errors = []

patterns = [
    re.compile(r'^\s*input\s+([^\s#]+)', re.IGNORECASE),
    re.compile(r'^\s*source\s+([^\s#]+)', re.IGNORECASE),
    re.compile(r'^\s*map-image\s+([^\s#]+)', re.IGNORECASE),
    re.compile(r'^\s*sketch\s+([^\s#]+)', re.IGNORECASE)
]

def check_file_refs(file_path):
    if not os.path.exists(file_path):
        return
    
    base_dir = os.path.dirname(file_path)
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                for p in patterns:
                    match = p.search(line)
                    if match:
                        ref_path = match.group(1).strip('"\'')
                        ref_path = ref_path.split(' ')[0]
                        full_ref_path = os.path.join(base_dir, ref_path)
                        
                        if not os.path.exists(full_ref_path):
                            # Identifikácia typu súboru
                            ext = os.path.splitext(ref_path)[1].lower()
                            file_type = "Iné"
                            if ext in ['.jpg', '.png', '.tif', '.gif', '.pdf', '.jpeg', '.tga']:
                                file_type = "Obrázok/Podklad"
                            elif ext in ['.th', '.th2', '.thconfig', '']:
                                file_type = "Therion súbor"
                            
                            errors.append({
                                'file': file_path.replace(DATA_ROOT, ''),
                                'line': line_num,
                                'ref': ref_path,
                                'type': file_type
                            })
                            if len(errors) >= MAX_ERRORS:
                                return True
    except Exception:
        pass
    return False

# Prechádzaj projekty
for project in os.listdir(DATA_ROOT):
    project_path = os.path.join(DATA_ROOT, project)
    if not os.path.isdir(project_path):
        continue
    
    for root, dirs, files in os.walk(project_path):
        # Filtrovanie ignorovaných adresárov
        dirs[:] = [d for d in dirs if d.lower() not in IGNORE_DIRS]
        
        for f in files:
            if f.endswith(('.th', '.th2', '.thconfig', 'thconfig')):
                if check_file_refs(os.path.join(root, f)):
                    break
        if len(errors) >= MAX_ERRORS:
            break
    if len(errors) >= MAX_ERRORS:
        break

print("| Súbor (kde je chyba) | Riadok | Odkazovaný chýbajúci súbor | Typ |")
print("| :--- | :--- | :--- | :--- |")
for e in errors:
    print(f"| {e['file']} | {e['line']} | {e['ref']} | {e['type']} |")
