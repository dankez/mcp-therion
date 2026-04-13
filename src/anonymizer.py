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
