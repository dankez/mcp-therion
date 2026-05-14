import pytest
from unittest.mock import patch, mock_open, MagicMock
import os
import subprocess
from src.server import read_anonymized_th, compile_therion

def test_read_anonymized_th_success():
    mock_content = "survey test\ncs lat-long\ndata normal from to length\n1 2 150.5\nendp"
    # Anonymized should remove 'cs lat-long' and replace '150.5' with '0'
    expected_partial = "1       2   0"
    
    with patch("builtins.open", mock_open(read_data=mock_content)):
        with patch("os.path.exists", return_value=True):
            result = read_anonymized_th("project/test.th")
            assert "cs lat-long" not in result
            assert expected_partial in result

def test_read_anonymized_th_error():
    with patch("builtins.open", side_effect=Exception("File not found")):
        result = read_anonymized_th("nonexistent.th")
        assert "Chyba pri čítaní súboru" in result

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
    with patch("os.path.exists", return_value=False):
        result = compile_therion("missing.th")
        assert "Chyba: Súbor missing.th neexistuje." in result
