#!/usr/bin/env python3
"""
Unit tests for the ProTox-3.0 API client parser logic (no network).

Covers CSV parsing against the documented ProTox-3.0 acute-toxicity CSV
layout and GHS class mapping from the NAR 2024 / FAQ table.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest

from services.protox_client import (
    _parse_protox_csv,
    _ghs_from_ld50,
    _fallback,
    _GHS_TABLE,
)

# Sample CSV mirroring the ProTox-3.0 acute-toxicity response (NAR 2024 FAQ):
# column-oriented with rows per prediction.
SAMPLE_CSV = (
    "input,type,Target,Prediction,Probability\n"
    "CCO,acute_tox,LD50,1000.0,100.00\n"
    "CCO,acute_tox,tox_class,4,100.00\n"
)


def test_parse_protox_csv_happy_path():
    parsed = _parse_protox_csv(SAMPLE_CSV)
    assert parsed is not None
    ld50, tox_class, accuracy = parsed
    assert ld50 == pytest.approx(1000.0)
    assert tox_class == 4
    assert accuracy == pytest.approx(100.0)


def test_parse_protox_csv_no_ld50_returns_none():
    assert _parse_protox_csv("Toxicity Class,3,Accuracy (%),50.0") is None
    assert _parse_protox_csv("") is None


def test_parse_protox_csv_non_numeric_tolerated():
    csv_text = "LD50 (mg/kg),n/a,Toxicity Class,2,Accuracy (%),70.5"
    parsed = _parse_protox_csv(csv_text)
    # LD50 missing (non-numeric) -> no LD50 row found -> None
    assert parsed is None


@pytest.mark.parametrize("ld50,expected_class", [
    (1.0, "I"), (10.0, "II"), (120.0, "III"),
    (1000.0, "IV"), (3500.0, "V"), (6000.0, "VI"),
])
def test_ghs_from_ld50_boundaries(ld50, expected_class):
    ghs = _ghs_from_ld50(ld50)
    assert ghs["category"] == expected_class
    assert "label" in ghs and "color" in ghs


def test_ghs_color_mapping():
    assert _ghs_from_ld50(1.0)["color"] == "RED"
    assert _ghs_from_ld50(100.0)["color"] == "ORANGE"
    assert _ghs_from_ld50(1000.0)["color"] == "YELLOW"
    assert _ghs_from_ld50(10000.0)["color"] == "GREEN"


def test_fallback_structure():
    fb = _fallback("CCO", "connection refused")
    assert fb["source"] == "ProTox-3.0-fallback"
    assert fb["ld50_mg_per_kg"] is None
    assert fb["confidence"] == "low"
    assert "connection refused" in fb["confidence_note"]


def test_ghs_table_has_six_classes():
    classes = [c for _, c, _ in _GHS_TABLE]
    assert classes == ["I", "II", "III", "IV", "V", "VI"]
