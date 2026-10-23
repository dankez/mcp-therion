from mcp.server.fastmcp import FastMCP
import os
import subprocess
import json
import re
import shutil
import glob
import struct
import urllib.parse
from src.anonymizer import anonymize_th

mcp = FastMCP("Therion Mentor")
DATA_ROOT = os.environ.get("THERION_DATA_ROOT", "/home/dankez/Downloads/dropbox-spolu/")
STUDNICA_PATH = "studnica.json"
SOURCES_DIR = "sources"

if not os.path.exists(SOURCES_DIR):
    os.makedirs(SOURCES_DIR)

def validate_path(rel_path: str):
    """Overí, či je cesta bezpečná a nachádza sa v DATA_ROOT."""
    abs_path = os.path.abspath(os.path.join(DATA_ROOT, rel_path))
    root_path = os.path.abspath(DATA_ROOT)
    if os.path.commonpath([root_path, abs_path]) != root_path:
        raise ValueError(f"Neplatná cesta: {rel_path}. Prístup mimo {DATA_ROOT} je zakázaný.")
    return abs_path

def find_therion_executable():
    """Deteguje lokálnu inštaláciu Therionu cez PATH alebo známe fallback cesty."""
    which_path = shutil.which("therion")
    if which_path:
        return which_path

    if os.name == 'nt' or 'WINDIR' in os.environ:
        program_files = [
            os.environ.get("ProgramFiles", "C:\\Program Files"),
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
            os.environ.get("LOCALAPPDATA", "") + "\\Programs"
        ]
        for pf in program_files:
            if pf:
                candidate = os.path.join(pf, "Therion", "therion.exe")
                if os.path.isfile(candidate):
                    return candidate

    unix_paths = [
        "/usr/bin/therion",
        "/usr/local/bin/therion",
        "/opt/homebrew/bin/therion",
        "/bin/therion"
    ]
    for p in unix_paths:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p

    return "therion"

def parse_therion_log(log_content: str) -> dict:
    """
    Vyhodnocuje log z Therionu pomocou regexov:
    - Nezhody projekcií (tiché zahodenia scrapov S -.-- @ ())
    - Varovania triangulátora (multiple scrap outer outlines not supported yet, invalid scrap outline)
    - TeX layout errory (! Emergency stop, problémy v legendbox s \\par)
    """
    result = {
        "projection_mismatches": [],
        "triangulator_warnings": [],
        "tex_errors": [],
        "raw_warnings": [],
        "raw_errors": []
    }

    if not log_content:
        return result

    proj_mismatch_pattern = re.compile(r"(S\s+-\.--\s+@\s+\(\)|scrap\s+dropped|projection\s+mismatch)", re.IGNORECASE)
    triangulator_pattern = re.compile(
        r"(multiple\s+scrap\s+outer\s+outlines\s+not\s+supported\s+yet|invalid\s+scrap\s+outline|self-intersecting|triangulation\s+error)",
        re.IGNORECASE
    )
    tex_pattern = re.compile(
        r"(!\s+Emergency\s+stop|legendbox.*\\par|!\s+TeX\s+error|!\s+Undefined\s+control\s+sequence)",
        re.IGNORECASE
    )

    for line in log_content.splitlines():
        line_clean = line.strip()
        if proj_mismatch_pattern.search(line_clean):
            result["projection_mismatches"].append(line_clean)
        if triangulator_pattern.search(line_clean):
            result["triangulator_warnings"].append(line_clean)
        if tex_pattern.search(line_clean):
            result["tex_errors"].append(line_clean)
        if re.search(r"\bwarning\b", line_clean, re.IGNORECASE):
            result["raw_warnings"].append(line_clean)
        if re.search(r"\berror\b|^\s*!\s+", line_clean, re.IGNORECASE):
            result["raw_errors"].append(line_clean)

    return result

def compute_polygon_area(coords):
    """Vypočíta orientovanú plochu polygónu. A > 0 => CCW, A < 0 => CW."""
    n = len(coords)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += coords[i][0] * coords[j][1]
        area -= coords[j][0] * coords[i][1]
    return area / 2.0

def parse_therion_2d(th2_content: str) -> dict:
    """
    Parser pre Therion 2D dáta (.th2 a .th kresbu):
    Extrahuje scraps, čiary (wall, border) a body (station) vrátane -outline, -reverse, -visibility.
    A vyhodnocuje orientáciu stien aj registračných bodov v rozdelených scrapoch.
    """
    scraps = []
    current_scrap = None
    current_line = None

    lines = th2_content.splitlines()
    for raw_line in lines:
        line_str = raw_line.strip()
        if not line_str or line_str.startswith("#"):
            continue

        m_scrap = re.match(r"^scrap\s+([^\s]+)", line_str)
        if m_scrap:
            current_scrap = {
                "id": m_scrap.group(1),
                "stations": [],
                "lines": []
            }
            scraps.append(current_scrap)
            continue

        if line_str == "endscrap":
            current_scrap = None
            current_line = None
            continue

        if current_scrap is None:
            continue

        if line_str.startswith("point"):
            m_st = re.search(r"point\s+([\d\.-]+)\s+([\d\.-]+)\s+station\s+.*-name\s+([^\s]+)", line_str)
            if m_st:
                x, y, name = float(m_st.group(1)), float(m_st.group(2)), m_st.group(3)
                vis = "-visibility off" not in line_str
                current_scrap["stations"].append({
                    "name": name,
                    "visibility": vis,
                    "coords": (x, y)
                })
            continue

        m_line = re.match(r"^line\s+([^\s]+)", line_str)
        if m_line:
            line_type = m_line.group(1)
            outline = "out"
            if "-outline in" in line_str:
                outline = "in"
            elif "-outline none" in line_str:
                outline = "none"
            elif "-outline out" in line_str:
                outline = "out"

            reverse = "-reverse on" in line_str
            current_line = {
                "type": line_type,
                "outline": outline,
                "reverse": reverse,
                "coords": []
            }
            current_scrap["lines"].append(current_line)
            continue

        if line_str == "endline":
            current_line = None
            continue

        if current_line is not None:
            tokens = line_str.split()
            nums = []
            for tok in tokens:
                try:
                    nums.append(float(tok))
                except ValueError:
                    pass
            for i in range(0, len(nums) - 1, 2):
                current_line["coords"].append((nums[i], nums[i+1]))

    warnings = []
    scraps_analysis = []

    for scrap in scraps:
        scrap_id = scrap["id"]
        stations = scrap["stations"]
        visible_stations = [s for s in stations if s["visibility"]]
        hidden_stations = [s for s in stations if not s["visibility"]]

        scrap_info = {
            "id": scrap_id,
            "total_stations": len(stations),
            "visible_stations": [s["name"] for s in visible_stations],
            "hidden_stations": [s["name"] for s in hidden_stations],
            "is_split_scrap_candidate": len(hidden_stations) > 0,
            "warnings": []
        }

        if len(stations) < 2:
            w = f"Scrap '{scrap_id}': Má menej ako 2 registračné body (celkovo {len(stations)}), hrozí strata transformácie."
            scrap_info["warnings"].append(w)
            warnings.append(w)

        for line in scrap["lines"]:
            if line["type"] in ["wall", "border"]:
                coords = line["coords"]
                if len(coords) >= 3:
                    area = compute_polygon_area(coords)
                    eff_area = -area if line["reverse"] else area
                    if line["outline"] == "out" and eff_area < 0:
                        w = f"Scrap '{scrap_id}': Čiara {line['type']} (out) má nesprávnu orientáciu (smer hodinových ručičiek namiesto proti smeru)."
                        scrap_info["warnings"].append(w)
                        warnings.append(w)
                    elif line["outline"] == "in" and eff_area > 0:
                        w = f"Scrap '{scrap_id}': Čiara {line['type']} (in) má nesprávnu orientáciu (smer proti smeru hodinových ručičiek namiesto v smere)."
                        scrap_info["warnings"].append(w)
                        warnings.append(w)

        scraps_analysis.append(scrap_info)

    return {
        "scraps": scraps_analysis,
        "warnings": warnings
    }

def point_in_triangle_2d(px, py, ax, ay, bx, by, cx, cy):
    """Barycentrická kontrola pre 2D bod v trojuholníku."""
    v0x, v0y = cx - ax, cy - ay
    v1x, v1y = bx - ax, by - ay
    v2x, v2y = px - ax, py - ay

    den = v0x * v1y - v1x * v0y
    if abs(den) < 1e-9:
        return False

    u = (v2x * v1y - v1x * v2y) / den
    v = (v0x * v2y - v2x * v0y) / den

    return (u >= -1e-5) and (v >= -1e-5) and (u + v <= 1.0 + 1e-5)

def parse_lox_binary(lox_data: bytes) -> list:
    """
    Parses binary Therion .lox file.
    Returns scraps list with points and triangles.
    """
    scraps = []
    offset = 0
    data_len = len(lox_data)

    while offset + 16 <= data_len:
        c_type, rec_size, count, payload_size = struct.unpack_from("<4I", lox_data, offset)
        offset += 16

        if c_type == 4: # Scrap chunk
            rec_bytes = count * rec_size
            records_data = lox_data[offset : offset + rec_bytes]
            payload_data = lox_data[offset + rec_bytes : offset + rec_bytes + payload_size]

            for i in range(count):
                rec = struct.unpack_from("<8I", records_data, i * 32)
                s_id, survey_id, num_pts, pts_off, pts_sz, num_tri, tri_off, tri_sz = rec

                points = []
                if pts_sz > 0 and num_pts > 0:
                    pts_raw = payload_data[pts_off : pts_off + pts_sz]
                    for p in range(num_pts):
                        if (p + 1) * 24 <= len(pts_raw):
                            x, y, z = struct.unpack_from("<3d", pts_raw, p * 24)
                            points.append((x, y, z))

                triangles = []
                if tri_sz > 0 and num_tri > 0:
                    tri_raw = payload_data[tri_off : tri_off + tri_sz]
                    for t in range(num_tri):
                        if (t + 1) * 12 <= len(tri_raw):
                            v1, v2, v3 = struct.unpack_from("<3I", tri_raw, t * 12)
                            triangles.append((v1, v2, v3))

                scraps.append({
                    "id": s_id,
                    "survey_id": survey_id,
                    "points": points,
                    "triangles": triangles
                })

        offset += rec_size * count + payload_size

    return scraps

def analyze_lox_coverage(lox_data: bytes, stations_dict: dict) -> dict:
    """
    Porovná súradnice meračských staníc voči trojuholníkom v .lox
    a reportuje stanice s nulovým plošným pokrytím.
    """
    scraps = parse_lox_binary(lox_data)
    all_triangles_2d = []
    for sc in scraps:
        pts = sc["points"]
        for tri in sc["triangles"]:
            v1, v2, v3 = tri
            if v1 < len(pts) and v2 < len(pts) and v3 < len(pts):
                p1, p2, p3 = pts[v1], pts[v2], pts[v3]
                all_triangles_2d.append((p1[0], p1[1], p2[0], p2[1], p3[0], p3[1]))

    coverage = {}
    uncovered = []
    for st_name, (sx, sy, sz) in stations_dict.items():
        is_covered = False
        for (ax, ay, bx, by, cx, cy) in all_triangles_2d:
            if point_in_triangle_2d(sx, sy, ax, ay, bx, by, cx, cy):
                is_covered = True
                break
        coverage[st_name] = is_covered
        if not is_covered:
            uncovered.append(st_name)

    return {
        "total_scraps": len(scraps),
        "total_triangles": len(all_triangles_2d),
        "total_stations_checked": len(stations_dict),
        "covered_stations_count": len(stations_dict) - len(uncovered),
        "uncovered_stations": uncovered,
        "coverage_ratio": (len(stations_dict) - len(uncovered)) / max(len(stations_dict), 1)
    }

def check_bbox_overlap(bbox1, bbox2):
    """Overí, či sa dva BBoxy (xmin, ymin, xmax, ymax) prekrývajú."""
    x1_min, y1_min, x1_max, y1_max = bbox1
    x2_min, y2_min, x2_max, y2_max = bbox2

    if x1_max <= x2_min or x2_max <= x1_min:
        return False
    if y1_max <= y2_min or y2_max <= y1_min:
        return False
    return True

def inspect_pdf_layout(legend_bbox: list, cave_bbox: list, has_header_white_mask: bool = True) -> dict:
    """
    Kontrola PDF layoutu: prekryv BBoxu legendy a BBoxu jaskyne, biela maska hlavičky.
    """
    overlap = check_bbox_overlap(legend_bbox, cave_bbox)
    warnings = []
    if overlap:
        warnings.append("Varovanie: Legenda sa prekrýva s kresbou/polygónom jaskyne!")
    if has_header_white_mask:
        warnings.append("Upozornenie: Biela maska hlavičky je aktívna - skontrolujte, či nezakrýva vetvy jaskyne pod hlavičkou.")

    return {
        "legend_bbox": legend_bbox,
        "cave_bbox": cave_bbox,
        "overlap_detected": overlap,
        "has_header_white_mask": has_header_white_mask,
        "warnings": warnings
    }

def query_zbgis_wms(layer_type: str, bbox: list, crs: str = "EPSG:5514", width: int = 800, height: int = 600) -> dict:
    """
    Pomocný nástroj na dopytovanie oficiálneho WMS ZBGIS (EPSG:5514 / JTSK / UTM)
    pre vrstevnice (contour) a reliéf (relief) s generovaním kalibračných metadát.
    """
    wms_endpoints = {
        "contour": "https://zbgisws.skgeodesy.sk/zbgis_vyskopis_wms_featureinfo/service.svc/get",
        "relief": "https://zbgisws.skgeodesy.sk/zbgis_dmr_wms/service.svc/get",
        "water": "https://zbgisws.skgeodesy.sk/zbgis_vodstvo_wms_featureinfo/service.svc/get",
        "roads": "https://zbgisws.skgeodesy.sk/zbgis_wms_featureinfo/service.svc/get"
    }

    layers_map = {
        "contour": "1",
        "relief": "1",
        "water": "5,6,7,14",
        "roads": "62,69"
    }

    endpoint = wms_endpoints.get(layer_type, wms_endpoints["contour"])
    layer_ids = layers_map.get(layer_type, "1")

    bbox_str = ",".join(str(x) for x in bbox)

    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetMap",
        "LAYERS": layer_ids,
        "STYLES": "",
        "CRS": crs,
        "BBOX": bbox_str,
        "WIDTH": str(width),
        "HEIGHT": str(height),
        "FORMAT": "image/png",
        "TRANSPARENT": "TRUE"
    }

    wms_url = endpoint + "?" + urllib.parse.urlencode(params)

    xmin, ymin, xmax, ymax = bbox
    scale_x = (xmax - xmin) / width
    scale_y = (ymax - ymin) / height

    calibration_metadata = {
        "crs": crs,
        "bbox": bbox,
        "width_px": width,
        "height_px": height,
        "pixel_size_x": scale_x,
        "pixel_size_y": scale_y,
        "affine_transform": [scale_x, 0, xmin, 0, -scale_y, ymax],
        "attribution": "GKÚ Bratislava / ZBGIS (CC BY 4.0)"
    }

    return {
        "layer_type": layer_type,
        "wms_url": wms_url,
        "calibration_metadata": calibration_metadata
    }

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
    try:
        full_path = validate_path(rel_path)
    except ValueError as e:
        return str(e)
    
    if not os.path.exists(full_path) and not rel_path.endswith('.thconfig'):
        potential_path = full_path + ""
        if not os.path.exists(potential_path):
             return f"Chyba: Súbor {rel_path} nebol nájdený."

    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if anonymize:
            return anonymize_th(content)
        return content
    except Exception as e:
        return f"Chyba pri čítaní súboru: {str(e)}"

def read_anonymized_th(rel_path: str):
    """Kompatibilný wrapper pre staršie testy."""
    return read_therion_file(rel_path, anonymize=True)

@mcp.tool()
def analyze_drawing_geometry(rel_path: str):
    """Statická analýza 2D kresby (.th2 alebo .th) bez nutnosti spúšťať celý kompilátor."""
    try:
        full_path = validate_path(rel_path)
    except ValueError as e:
        return str(e)

    if not os.path.exists(full_path):
        return f"Chyba: Súbor {rel_path} nebol nájdený."

    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        analysis = parse_therion_2d(content)
        return json.dumps(analysis, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Chyba pri analýze kresby: {str(e)}"

@mcp.tool()
def analyze_lox_model(lox_rel_path: str, stations_json: str):
    """
    Diagnostika 3D LOX modelov: Porovná súradnice meračských staníc z .th voči trojuholníkom v .lox
    a reportuje stanice s nulovým plošným pokrytím.
    stations_json je JSON reťazec napr. '{"1": [10.0, 20.0, 0.0], "2": [100.0, 100.0, 0.0]}'
    """
    try:
        lox_full_path = validate_path(lox_rel_path)
    except ValueError as e:
        return str(e)

    if not os.path.exists(lox_full_path):
        return f"Chyba: Súbor {lox_rel_path} nebol nájdený."

    try:
        stations_dict = json.loads(stations_json)
    except Exception as e:
        return f"Chyba pri dekódovaní JSON staníc: {str(e)}"

    try:
        with open(lox_full_path, 'rb') as f:
            lox_data = f.read()
        result = analyze_lox_coverage(lox_data, stations_dict)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Chyba pri analýze LOX modelu: {str(e)}"

@mcp.tool()
def check_pdf_layout_overlap(legend_bbox_json: str, cave_bbox_json: str, has_header_white_mask: bool = True):
    """
    Kontrola finálneho PDF layoutu: detekcia prekryvu BBoxu legendy a BBoxu jaskyne,
    a kontrola bielej masky hlavičky.
    BBoxy sú JSON zoznamy [xmin, ymin, xmax, ymax].
    """
    try:
        legend_bbox = json.loads(legend_bbox_json)
        cave_bbox = json.loads(cave_bbox_json)
        result = inspect_pdf_layout(legend_bbox, cave_bbox, has_header_white_mask)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Chyba pri kontrole PDF layoutu: {str(e)}"

@mcp.tool()
def query_zbgis_terrain_wms(layer_type: str, bbox_json: str, crs: str = "EPSG:5514", width: int = 800, height: int = 600):
    """
    Pomocný nástroj na dopytovanie ZBGIS WMS (EPSG:5514 / JTSK / UTM) pre vrstevnice (contour)
    a reliéf (relief) s generovaním kalibračných metadát.
    bbox_json je JSON zoznam [xmin, ymin, xmax, ymax].
    """
    try:
        bbox = json.loads(bbox_json)
        result = query_zbgis_wms(layer_type, bbox, crs, width, height)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Chyba pri dopytovaní ZBGIS WMS: {str(e)}"

@mcp.tool()
def list_therion_projects():
    """Zoznam projektov v dátovom úložisku."""
    if not os.path.exists(DATA_ROOT):
        return f"Chyba: {DATA_ROOT} neexistuje."
    return [d for d in os.listdir(DATA_ROOT) if os.path.isdir(os.path.join(DATA_ROOT, d))]

@mcp.tool()
def compile_therion(rel_path: str):
    """Spustí kompiláciu Therion lokálne a vráti výsledok spolu s diagnostikou logov."""
    try:
        full_path = validate_path(rel_path)
    except ValueError as e:
        return str(e)

    dir_path = os.path.dirname(full_path)
    file_name = os.path.basename(full_path)
    therion_bin = find_therion_executable()
    
    try:
        result = subprocess.run(
            [therion_bin, file_name],
            cwd=dir_path,
            capture_output=True,
            text=True,
            timeout=60
        )

        log_path = os.path.join(dir_path, "therion.log")
        log_diagnostics = {}
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as lf:
                    log_diagnostics = parse_therion_log(lf.read())
            except Exception:
                pass

        if result.returncode == 0:
            msg = "Kompilácia úspešná."
            if log_diagnostics and any(log_diagnostics.values()):
                msg += f"\nDiagnostika logu:\n{json.dumps(log_diagnostics, ensure_ascii=False, indent=2)}"
            return msg

        err_msg = f"Chyba pri kompilácii:\n{result.stderr}"
        if log_diagnostics and any(log_diagnostics.values()):
            err_msg += f"\nDiagnostika logu:\n{json.dumps(log_diagnostics, ensure_ascii=False, indent=2)}"
        return err_msg
    except Exception as e:
        return f"Interná chyba: {str(e)}"

@mcp.tool()
def generate_th2_skeleton(description: str):
    """Vygeneruje logickú kostru .th2 súboru."""
    return f"layout local\n  scale 1 100\nendlayout\n\n# Kostra: {description}\nscrap scrap1 -projection plan\n  line wall\n    10 10\n    20 10\n    20 20\n    10 20\n    10 10\n  endline\nendscrap"

if __name__ == "__main__":
    mcp.run()
