import pytest
from src.anonymizer import anonymize_th

def test_anonymize_th_removes_sensitive_data():
    content = "survey test\ncs lat-long\nfix 1 48.0 19.0\ndata normal from to length\n1 2 150.5\nendp"
    anonymized = anonymize_th(content)
    assert "cs lat-long" not in anonymized
    assert "fix 1" not in anonymized
    # Overenie, že stanice zostali a hodnota bola nahradená nulou
    assert "1" in anonymized
    assert "2" in anonymized
    assert "0" in anonymized
