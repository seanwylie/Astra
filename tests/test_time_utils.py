# tests/test_time_utils.py
# Temporal constraint line: presence and format only (no exact wording).

import re

import pytest

from utils.time_utils import temporal_constraint_line

# YYYY-MM-DD pattern; assert format, not wording
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


def test_temporal_constraint_line_presence():
    """The constraint line exists and is non-empty."""
    line = temporal_constraint_line()
    assert isinstance(line, str)
    assert len(line.strip()) > 0


def test_temporal_constraint_line_format():
    """The constraint line contains a date in YYYY-MM-DD format."""
    line = temporal_constraint_line()
    assert DATE_PATTERN.search(line), "constraint line should contain a YYYY-MM-DD date"
