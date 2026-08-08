import pytest
import os
from src.server import validate_path, DATA_ROOT, read_therion_file, compile_therion
from unittest.mock import patch, MagicMock

def test_validate_path_safe():
    # Should not raise ValueError
    rel_path = "project/file.th"
    expected = os.path.abspath(os.path.join(DATA_ROOT, rel_path))
    assert validate_path(rel_path) == expected

def test_validate_path_traversal():
    # Should raise ValueError
    rel_path = "../../etc/passwd"
    with pytest.raises(ValueError, match="Prístup mimo"):
        validate_path(rel_path)

def test_validate_path_absolute_traversal():
    # Should raise ValueError even if it starts with a slash if it's not under DATA_ROOT
    rel_path = "/etc/passwd"
    with pytest.raises(ValueError, match="Prístup mimo"):
        validate_path(rel_path)

def test_read_therion_file_traversal():
    result = read_therion_file("../../secret.txt")
    assert "Prístup mimo" in result

def test_compile_therion_traversal():
    result = compile_therion("../../../bin/ls")
    assert "Prístup mimo" in result

# Test for the downloader logic (logic copied from download_archives.py)
def test_downloader_sanitization():
    # import requests # Removed because it's not needed for this logic test
    import re

    # Mocking logic
    malicious_filenames = ["../../malicious.txt.gz", "normal.txt.gz", "/absolute/path/file.txt.gz"]

    for fname in malicious_filenames:
        safe_fname = os.path.basename(fname)
        # It should not contain any path separators
        assert "/" not in safe_fname
        assert "\\" not in safe_fname
        # For the malicious one, it should just be the filename
        if fname == "../../malicious.txt.gz":
            assert safe_fname == "malicious.txt.gz"
        if fname == "/absolute/path/file.txt.gz":
            assert safe_fname == "file.txt.gz"
