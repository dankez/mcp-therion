import pytest
from src.anonymizer import anonymize_th

def test_anonymize_point():
    content = "point 10.0 20.0 station"
    anonymized = anonymize_th(content)
    assert "10.0" not in anonymized
    assert "20.0" not in anonymized
    assert "0" in anonymized
    assert "station" in anonymized

def test_anonymize_point_negative():
    content = "point -5.5 0.0 type"
    anonymized = anonymize_th(content)
    assert "-5.5" not in anonymized
    assert "0.0" not in anonymized
    assert "0" in anonymized
    assert "type" in anonymized

def test_anonymize_scrap():
    content = "scrap my_scrap -name 1"
    anonymized = anonymize_th(content)
    assert "my_scrap" in anonymized
    assert "1" not in anonymized
    assert "0" in anonymized

def test_anonymize_bare_coordinates():
    content = "  1207.25 -434.75"
    anonymized = anonymize_th(content)
    assert "1207.25" not in anonymized
    assert "-434.75" not in anonymized
    assert "0" in anonymized

def test_anonymize_bare_coordinates_multiple():
    content = "-100.0 200.0 300.5"
    anonymized = anonymize_th(content)
    assert "-100.0" not in anonymized
    assert "200.0" not in anonymized
    assert "300.5" not in anonymized
    assert "0 0 0" in anonymized

def test_anonymize_mixed_content():
    content = "survey test\n  10.0 20.0\npoint 5.0 6.0 st1\nend survey"
    anonymized = anonymize_th(content)
    assert "survey test" in anonymized
    assert "10.0" not in anonymized
    assert "20.0" not in anonymized
    assert "5.0" not in anonymized
    assert "6.0" not in anonymized
    assert "st1" in anonymized or "st0" in anonymized # depends on implementation
    assert "end survey" in anonymized

def test_anonymize_preserves_unrelated_lines():
    content = "line wall\n  10 10\n  20 20\nendline"
    anonymized = anonymize_th(content)
    # Lines starting with 'line' are NOT currently anonymized by the 'point'/'scrap' rule
    # but the coordinates inside ARE anonymized by the bare coordinates rule if they match.
    assert "line wall" in anonymized
    assert "10" not in anonymized
    assert "20" not in anonymized
    assert "0 0" in anonymized
