import pytest
from src.server import generate_th2_skeleton

def test_generate_th2_skeleton_content():
    description = "Nova jaskyna"
    result = generate_th2_skeleton(description)
    
    assert "layout local" in result
    assert "scale 1 100" in result
    assert f"# Kostra: {description}" in result
    assert "scrap scrap1 -projection plan" in result
    assert "line wall" in result
    assert "10 10" in result
    assert "endline" in result
    assert "endscrap" in result
