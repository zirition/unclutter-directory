import pytest

from unclutter_directory.commons.parsers import parse_size, parse_time
from unclutter_directory.commons.validations import validate_rules_file


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("1KB", 1024),
        ("1MB", 1048576),
        ("1GB", 1073741824),
        ("1024", 1024),
        ("1 KB", 1024),
        ("1kb", 1024),
    ],
)
def test_parse_size_valid(input_str, expected):
    assert parse_size(input_str) == expected


def test_parse_size_invalid():
    with pytest.raises(ValueError):
        parse_size("invalid")


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("1s", 1),
        ("1m", 60),
        ("1h", 3600),
        ("1d", 86400),
        ("60", 60),
        ("1 h", 3600),
    ],
)
def test_parse_time_valid(input_str, expected):
    assert parse_time(input_str) == expected


def test_parse_time_invalid():
    with pytest.raises(ValueError):
        parse_time("invalid")


valid_rules = [
    {
        "conditions": {"larger": "1KB", "newer": "1d"},
        "action": {"type": "move", "target": "/path/to/target"},
        "check_archive": True,
    },
    {
        "conditions": {"larger": "10MB"},
        "action": {"type": "move", "target": "/path/to/target"},
    },
    {"conditions": {"contain": "keyword"}, "action": {"type": "delete"}},
    {
        "conditions": {"regex": "[a-z+]"},
        "action": {"type": "compress", "target": "."},
    },
    {
        "conditions": {"larger": "10MB"},
        "action": {"type": "delete"},
    },
    {
        "conditions": {"larger": "10MB"},
        "action": {"type": "compress", "target": "."},
    },
    {
        "conditions": {"larger": "10MB"},
        "action": {"type": "delete"},
        "check_archive": False,
    },
    {
        "conditions": {"larger": "10MB"},
        "action": {"type": "delete"},
        "check_archive": True,
    },
]


@pytest.mark.parametrize("rule", valid_rules)
def test_validate_rules_valid(rule):
    assert validate_rules_file([rule]) == []


invalid_rules_cases = [
    ("not a list", None),
    ("not a dict", None),
    ({"conditions": "not a dict"}, None),
    ({"conditions": {"invalid": "value"}}, None),
    ({"conditions": {"larger": "invalid"}}, None),
    ({"conditions": {"newer": "invalid"}}, None),
    ({"conditions": {"regex": "["}}, None),
    ({"action": "not a dict"}, None),
    ({"conditions": {"larger": "10MB"}, "action": {"type": "invalid"}}, None),
    ({"conditions": {"larger": "10MB"}, "action": {"type": "move"}}, "'target'"),
    ({"check_archive": "not a bool"}, "must be boolean"),
    ({"conditions": {"invalid_condition": "10MB"}, "action": {}}, None),
    ({"conditions": {"larger": "abc"}, "action": {}}, None),
    ({"conditions": {"older": "abc"}, "action": {}}, None),
    ({"conditions": {"regex": "[invalid[regex]"}, "action": {}}, None),
    ({"conditions": {"larger": "10MB"}, "action": {}}, None),
    ({"conditions": {"larger": "10MB"}, "action": {"type": "invalid_type"}}, None),
    ({"conditions": {"larger": "10MB"}, "action": {"type": "move"}}, "'target'"),
    (
        {
            "conditions": {"larger": "10MB"},
            "action": {"type": "delete"},
            "check_archive": 42,
        },
        "must be boolean",
    ),
]


@pytest.mark.parametrize("rule, expected_error", invalid_rules_cases)
def test_validate_rules_invalid(rule, expected_error):
    errors = validate_rules_file([rule])
    assert len(errors) > 0
    if expected_error:
        assert any(expected_error in error for error in errors)


@pytest.mark.parametrize(
    "rule, expected_error_count, expected_error_substring",
    [
        (
            {
                "conditions": {"larger": "10MB"},
                "action": {"type": "delete"},
                "delete_unpacked_on_match": True,
            },
            0,
            None,
        ),
        (
            {
                "conditions": {"larger": "10MB"},
                "action": {"type": "delete"},
                "delete_unpacked_on_match": False,
            },
            0,
            None,
        ),
        (
            {
                "conditions": {"larger": "10MB"},
                "action": {"type": "delete"},
                "delete_unpacked_on_match": "string",
            },
            1,
            "'delete_unpacked_on_match' must be boolean",
        ),
        (
            {
                "conditions": {"larger": "10MB"},
                "action": {"type": "delete"},
            },
            0,
            None,
        ),
    ],
)
def test_validate_rules_delete_unpacked_on_match(
    rule, expected_error_count, expected_error_substring
):
    errors = validate_rules_file([rule])
    assert len(errors) == expected_error_count
    if expected_error_substring:
        assert expected_error_substring in errors[0]
