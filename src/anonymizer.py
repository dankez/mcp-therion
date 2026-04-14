import re

def anonymize_th(content):
    # Odstránenie citlivých riadkov a meta-dát XTherionu
    sensitive_patterns = [
        r'^cs\s+.*', 
        r'^fix\s+.*', 
        r'^explo\s+.*', 
        r'^date\s+.*', 
        r'^team\s+.*', 
        r'^author\s+.*',
        r'^##XTHERION##.*'
    ]
    
    lines = content.splitlines()
    filtered_lines = []
    
    in_data_normal = False
    for line in lines:
        stripped = line.strip()
        
        # Preskočenie citlivých metadát
        if any(re.match(p, stripped) for p in sensitive_patterns):
            continue
        
        # Špeciálne spracovanie bloku 'data normal' (v .th súboroch)
        if "data normal" in stripped:
            in_data_normal = True
            filtered_lines.append(line)
            continue
            
        if in_data_normal and stripped and not stripped.startswith('end'):
            parts = line.split()
            if len(parts) > 2:
                # Názvy staníc (prvé dve slová) ponecháme, zvyšok nuly
                new_line = f"      {parts[0]}       {parts[1]}   " + " ".join(["0"] * (len(parts) - 2))
                filtered_lines.append(new_line)
                continue
        
        if stripped.startswith('end'):
            in_data_normal = False
            
        # Anonymizácia súradníc v .th2 (príkazy point, line, scrap a holé súradnice)
        # 1. Nahradenie čísel v riadkoch začínajúcich na 'point' alebo 'scrap' (okrem názvov)
        if stripped.startswith('point') or stripped.startswith('scrap'):
            # Nahradíme všetky číselné hodnoty (ktoré nie sú súčasťou názvov)
            # Pre jednoduchosť nahradíme všetky čísla v týchto riadkoch nulami, ak nasledujú po kľúčovom slove
            new_line = re.sub(r'(-?\d+(\.\d+)?)', '0', line)
            filtered_lines.append(new_line)
            continue

        # 2. Nahradenie holých súradníc (napr. "1207.25 -434.75")
        if re.match(r'^\s*-?\d+(\.\d+)?\s+-?\d+(\.\d+)?.*$', stripped):
            new_line = re.sub(r'(-?\d+(\.\d+)?)', '0', line)
            filtered_lines.append(new_line)
            continue

        filtered_lines.append(line)
        
    return "\n".join(filtered_lines)
