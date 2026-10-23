import pytest
from unittest.mock import patch, mock_open, MagicMock
import os
import subprocess
from src.server import read_therion_file, compile_therion

def test_read_anonymized_th_success():
    mock_content = "survey test\ncs lat-long\ndata normal from to length\n1 2 150.5\nendp"
    # Anonymized should remove 'cs lat-long' and replace '150.5' with '0'
    expected_partial = "1       2   0"
    
    with patch("builtins.open", mock_open(read_data=mock_content)):
        with patch("os.path.exists", return_value=True):
            result = read_therion_file("project/test.th", anonymize=True)
            assert "cs lat-long" not in result
            assert expected_partial in result

def test_read_anonymized_th_error():
    # File exists but open fails
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", side_effect=Exception("File not found")):
            result = read_therion_file("nonexistent.th", anonymize=True)
            assert "Chyba pri čítaní súboru: File not found" in result

def test_compile_therion_success():
    with patch("os.path.exists", return_value=True):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")
            result = compile_therion("project/main.th")
            assert result == "Kompilácia úspešná."
            mock_run.assert_called_once_with(
                ['therion', 'main.th'],
                cwd=os.path.dirname(os.path.join("/home/dankez/Downloads/dropbox-spolu/", "project/main.th")),
                capture_output=True,
                text=True,
                timeout=60
            )

def test_compile_therion_error():
    with patch("os.path.exists", return_value=True):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="Syntax error at line 5")
            result = compile_therion("project/main.th")
            assert "Chyba pri kompilácii" in result
            assert "Syntax error at line 5" in result

def test_compile_therion_not_found():
    # compile_therion does not explicitly check if the file exists, it relies on subprocess.run failure
    # if the directory doesn't exist.
    with patch("os.path.exists", return_value=True):
        with patch("subprocess.run", side_effect=Exception("No such file or directory")):
            result = compile_therion("missing.th")
            assert "Interná chyba" in result

def test_find_therion_executable():
    from src.server import find_therion_executable
    path = find_therion_executable()
    assert isinstance(path, str)
    assert len(path) > 0

def test_parse_therion_log():
    from src.server import parse_therion_log
    sample_log = """
    Therion 6.0.5
    S -.-- @ ()
    therion: warning -- multiple scrap outer outlines not supported yet
    therion: warning -- invalid scrap outline
    ! Emergency stop
    legendbox \par error
    """
    diag = parse_therion_log(sample_log)
    assert "S -.-- @ ()" in diag["projection_mismatches"]
    assert any("multiple scrap outer outlines" in w for w in diag["triangulator_warnings"])
    assert any("invalid scrap outline" in w for w in diag["triangulator_warnings"])
    assert any("Emergency stop" in e for e in diag["tex_errors"])
    assert any("legendbox" in e for e in diag["tex_errors"])

def test_parse_therion_2d_and_analyze():
    from src.server import parse_therion_2d
    sample_th2 = """
    scrap scrap1 -projection plan
      point 10 20 station -name 1
      point 50 20 station -name 2 -visibility off
      line wall -outline out
        0 0
        0 10
        10 10
        10 0
        0 0
      endline
    endscrap
    """
    res = parse_therion_2d(sample_th2)
    assert len(res["scraps"]) == 1
    scrap = res["scraps"][0]
    assert scrap["id"] == "scrap1"
    assert "1" in scrap["visible_stations"]
    assert "2" in scrap["hidden_stations"]
    assert scrap["is_split_scrap_candidate"] is True
    assert any("nesprávnu orientáciu" in w for w in res["warnings"])

def test_analyze_lox_coverage():
    import struct
    from src.server import analyze_lox_coverage

    # Binary LOX chunk
    hdr = struct.pack("<4I", 4, 32, 1, 84)
    rec = struct.pack("<8I", 1, 0, 3, 0, 72, 1, 72, 12)
    pts_data = struct.pack("<3d", 0.0, 0.0, 0.0) + struct.pack("<3d", 10.0, 0.0, 0.0) + struct.pack("<3d", 0.0, 10.0, 0.0)
    tri_data = struct.pack("<3I", 0, 1, 2)
    dummy_lox = hdr + rec + pts_data + tri_data

    stations = {
        "A1": (2.0, 2.0, 0.0),
        "A2": (50.0, 50.0, 0.0)
    }

    result = analyze_lox_coverage(dummy_lox, stations)
    assert result["total_scraps"] == 1
    assert result["total_triangles"] == 1
    assert result["covered_stations_count"] == 1
    assert "A2" in result["uncovered_stations"]
    assert result["coverage_ratio"] == 0.5

def test_inspect_pdf_layout():
    from src.server import inspect_pdf_layout
    res = inspect_pdf_layout([0, 0, 100, 100], [50, 50, 200, 200], has_header_white_mask=True)
    assert res["overlap_detected"] is True
    assert res["has_header_white_mask"] is True
    assert len(res["warnings"]) == 2

def test_query_zbgis_wms():
    from src.server import query_zbgis_wms
    res = query_zbgis_wms("contour", [-500000, -1300000, -490000, -1290000])
    assert res["layer_type"] == "contour"
    assert "LAYERS=1" in res["wms_url"]
    assert res["calibration_metadata"]["crs"] == "EPSG:5514"
    assert res["calibration_metadata"]["pixel_size_x"] == 12.5
