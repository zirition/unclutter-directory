from datetime import timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from unclutter_directory.entities.compressed_archive import CompressedArchive
from unclutter_directory.entities.file import File
from unclutter_directory.file_operations.file_matcher import FileMatcher


@pytest.fixture
def data():
    file1 = File(
        path=Path("/some/path"),
        name="example1.txt",
        date=timedelta(hours=1.5).total_seconds(),
        size=1000,
    )
    file2 = File(
        path=Path("/some/path"),
        name="example2.zip",
        date=timedelta(hours=1).total_seconds(),
        size=2000,
    )

    file_in_zip = File(
        path=Path("/archive/path"),
        name="inside.txt",
        date=timedelta(seconds=0).total_seconds(),
        size=500,
    )

    rule_name_start = {"conditions": {"start": "example"}}
    rule_name_end = {"conditions": {"end": ".txt"}}
    rule_name_contain = {"conditions": {"contain": "1"}}
    rule_name_regex = {"conditions": {"regex": "^exampl.*"}}
    rule_size_larger = {"conditions": {"larger": "500B"}}
    rule_size_smaller = {"conditions": {"smaller": "150001B"}}
    rule_age_older = {"conditions": {"older": "1h"}}
    rule_age_newer = {"conditions": {"newer": "2h"}}

    return {
        "file1": file1,
        "file2": file2,
        "file_in_zip": file_in_zip,
        "rule_name_start": rule_name_start,
        "rule_name_end": rule_name_end,
        "rule_name_contain": rule_name_contain,
        "rule_name_regex": rule_name_regex,
        "rule_size_larger": rule_size_larger,
        "rule_size_smaller": rule_size_smaller,
        "rule_age_older": rule_age_older,
        "rule_age_newer": rule_age_newer,
    }


def test_match_name_start(data):
    file1 = data["file1"]
    rule_name_start = data["rule_name_start"]
    matcher = FileMatcher([rule_name_start])
    matched_rule = matcher.match(file1)
    assert matched_rule is not None
    assert matched_rule == rule_name_start


def test_match_name_end(data):
    file1 = data["file1"]
    rule_name_end = data["rule_name_end"]
    matcher = FileMatcher([rule_name_end])
    matched_rule = matcher.match(file1)
    assert matched_rule is not None
    assert matched_rule == rule_name_end


def test_match_name_contain(data):
    file1 = data["file1"]
    rule_name_contain = data["rule_name_contain"]
    matcher = FileMatcher([rule_name_contain])
    matched_rule = matcher.match(file1)
    assert matched_rule is not None
    assert matched_rule == rule_name_contain


def test_match_name_regex(data):
    file2 = data["file2"]
    rule_name_regex = data["rule_name_regex"]
    matcher = FileMatcher([rule_name_regex])
    matched_rule = matcher.match(file2)
    assert matched_rule is not None
    assert matched_rule == rule_name_regex


def test_match_size_larger(data):
    file1 = data["file1"]
    rule_size_larger = data["rule_size_larger"]
    matcher = FileMatcher([rule_size_larger])
    matched_rule = matcher.match(file1)
    assert matched_rule is not None
    assert matched_rule == rule_size_larger


def test_match_size_smaller(data):
    file1 = data["file1"]
    rule_size_smaller = data["rule_size_smaller"]
    matcher = FileMatcher([rule_size_smaller])
    matched_rule = matcher.match(file1)
    assert matched_rule is not None
    assert matched_rule == rule_size_smaller


def test_match_age_older(data):
    file1 = data["file1"]
    rule_age_older = data["rule_age_older"]
    matcher = FileMatcher([rule_age_older])
    matched_rule = matcher.match(file1)
    assert matched_rule is not None
    assert matched_rule == rule_age_older


def test_match_age_newer(data):
    file1 = data["file1"]
    rule_age_newer = data["rule_age_newer"]
    matcher = FileMatcher([rule_age_newer])
    matched_rule = matcher.match(file1)
    assert matched_rule is not None
    assert matched_rule == rule_age_newer


def test_no_match(data):
    file1 = data["file1"]
    matcher = FileMatcher([{"conditions": {"start": "non_existing"}}])
    matched_rule = matcher.match(file1)
    assert matched_rule is None


def test_archive_match(data):
    file2 = data["file2"]
    file_in_zip = data["file_in_zip"]
    with patch(
        "unclutter_directory.file_operations.file_matcher.get_archive_manager"
    ) as mock_get_archive:
        mock_archive_manager = MagicMock(spec=CompressedArchive)
        mock_archive_manager.get_files.return_value = [file_in_zip]
        mock_get_archive.return_value = mock_archive_manager

        rule_check_archive = {
            "conditions": {"start": "inside"},
            "check_archive": True,
        }
        matcher = FileMatcher([rule_check_archive])
        matched_rule = matcher.match(file2)
        assert matched_rule is not None
        assert matched_rule == rule_check_archive


def test_match_name_start_case_insensitive(data):
    rule_name_start = data["rule_name_start"]
    file1_upper = File(
        path=Path("/some/path"),
        name="EXAMPLE1.TXT",
        date=timedelta(hours=1.5).total_seconds(),
        size=1000,
    )
    matcher = FileMatcher([rule_name_start])
    matched_rule = matcher.match(file1_upper)
    assert matched_rule is not None
    assert matched_rule == rule_name_start


def test_match_name_end_case_insensitive(data):
    rule_name_end = data["rule_name_end"]
    file1_upper = File(
        path=Path("/some/path"),
        name="EXAMPLE2.TXT",
        date=timedelta(hours=1.5).total_seconds(),
        size=1000,
    )
    matcher = FileMatcher([rule_name_end])
    matched_rule = matcher.match(file1_upper)
    assert matched_rule is not None
    assert matched_rule == rule_name_end


def test_match_name_contain_case_insensitive(data):
    rule_name_contain = data["rule_name_contain"]
    file1_mixed = File(
        path=Path("/some/path"),
        name="Example1.txt",
        date=timedelta(hours=1.5).total_seconds(),
        size=1000,
    )
    matcher = FileMatcher([rule_name_contain])
    matched_rule = matcher.match(file1_mixed)
    assert matched_rule is not None
    assert matched_rule == rule_name_contain


def test_match_name_regex_case_insensitive(data):
    rule_name_regex = data["rule_name_regex"]
    file2_upper = File(
        path=Path("/some/path"),
        name="EXAMPL2.ZIP",
        date=timedelta(hours=1).total_seconds(),
        size=2000,
    )
    matcher = FileMatcher([rule_name_regex])
    matched_rule = matcher.match(file2_upper)
    assert matched_rule is not None
    assert matched_rule == rule_name_regex


def test_match_name_start_case_sensitive(data):
    file1_upper = File(
        path=Path("/some/path"),
        name="EXAMPLE1.TXT",
        date=timedelta(hours=1.5).total_seconds(),
        size=1000,
    )
    matcher = FileMatcher(
        [{"conditions": {"start": "example"}, "case_sensitive": True}]
    )
    matched_rule = matcher.match(file1_upper)
    assert matched_rule is None


def test_match_name_end_case_sensitive(data):
    file1_upper = File(
        path=Path("/some/path"),
        name="EXAMPLE1.TXT",
        date=timedelta(hours=1.5).total_seconds(),
        size=1000,
    )
    matcher = FileMatcher([{"conditions": {"end": ".txt"}, "case_sensitive": True}])
    matched_rule = matcher.match(file1_upper)
    assert matched_rule is None


def test_match_name_contain_case_sensitive(data):
    file1_upper = File(
        path=Path("/some/path"),
        name="EXAMPLE1.TXT",
        date=timedelta(hours=1.5).total_seconds(),
        size=1000,
    )
    matcher = FileMatcher(
        [{"conditions": {"contain": "xample1"}, "case_sensitive": True}]
    )
    matched_rule = matcher.match(file1_upper)
    assert matched_rule is None


def test_match_name_regex_case_sensitive(data):
    file1_upper = File(
        path=Path("/some/path"),
        name="EXAMPLE1.TXT",
        date=timedelta(hours=1.5).total_seconds(),
        size=1000,
    )
    matcher = FileMatcher(
        [{"conditions": {"regex": "^exampl.*"}, "case_sensitive": True}]
    )
    matched_rule = matcher.match(file1_upper)
    assert matched_rule is None
