import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from unclutter_directory.config.organize_config import OrganizeConfig
from unclutter_directory.validation.rules_validator import RulesFileValidator


@pytest.fixture
def validator():
    return RulesFileValidator()


@pytest.fixture
def temp_dir():
    t = tempfile.TemporaryDirectory()
    yield Path(t.name)
    t.cleanup()


@pytest.fixture
def target_dir(temp_dir):
    return temp_dir


@pytest.fixture
def make_config(target_dir):
    def inner(rules_file=None):
        return OrganizeConfig(
            target_dir=target_dir,
            rules_file=rules_file,
            dry_run=False,
            quiet=False,
            always_delete=False,
            never_delete=False,
            include_hidden=False,
        )

    return inner


def test_no_rules_file_and_no_default(make_config, validator):
    config = make_config(rules_file=None)
    # No default file created
    errors = validator.validate(config)
    assert (
        "No rules file specified and no default .unclutter_rules.yaml found in target directory"
        in errors
    )


def test_rules_file_not_exist(make_config, validator):
    config = make_config(rules_file="/nonexistent.yaml")
    errors = validator.validate(config)
    assert any("does not exist" in e for e in errors)


def test_rules_file_is_directory(make_config, validator, target_dir):
    # Test with a directory path
    config = make_config(rules_file=str(target_dir))
    errors = validator.validate(config)
    assert any("not a regular file" in e for e in errors)


def test_rules_file_too_large(make_config, validator):
    # Create a temporary file larger than 10MB limit
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"0" * (11 * 1024 * 1024))  # 11MB
        large_file_path = f.name
    try:
        config = make_config(rules_file=large_file_path)
        errors = validator.validate(config)
        assert any("too large" in e for e in errors)
    finally:
        Path(large_file_path).unlink(missing_ok=True)


def test_rules_file_empty(make_config, validator):
    # Create an empty temporary file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        empty_file_path = f.name
    try:
        config = make_config(rules_file=empty_file_path)
        errors = validator.validate(config)
        assert any("empty" in e for e in errors)
    finally:
        Path(empty_file_path).unlink(missing_ok=True)


def test_rules_file_not_readable(make_config, validator):
    # Create a temporary file with no read permissions
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"some content")
        no_read_file = f.name
    os.chmod(no_read_file, 0o200)  # write only
    try:
        config = make_config(rules_file=no_read_file)
        errors = validator.validate(config)
        assert any("not readable" in e for e in errors)
    finally:
        os.chmod(no_read_file, 0o600)  # restore read permission to allow deletion
        Path(no_read_file).unlink(missing_ok=True)


def test_load_rules_invalid_yaml(make_config, validator, target_dir):
    # Create default file with invalid YAML content
    default_file = target_dir / ".unclutter_rules.yaml"
    default_file.write_text("invalid: [unclosed")
    config = make_config(rules_file=None)  # Will auto-detect default file
    errors = validator.validate(config)
    assert any("Failed to load rules" in e or "Unexpected error" in e for e in errors)


def test_load_rules_empty_or_not_list(make_config, validator, target_dir):
    # Test empty file with whitespace
    config = make_config(rules_file=None)
    default_file = target_dir / ".unclutter_rules.yaml"
    default_file.write_text("   ")  # whitespace only, triggers internal empty check
    config.rules_file = str(default_file)
    errors = validator.validate(config)
    assert any("Failed to load rules" in e for e in errors)

    # Test non-list content
    default_file.write_text("key: value")
    config.rules_file = str(default_file)
    errors = validator.validate(config)
    assert any("Failed to load rules" in e for e in errors)


@patch("unclutter_directory.commons.validate_rules_file")
def test_rules_file_with_validation_errors(
    mock_validate_rules_file, make_config, validator, target_dir
):
    config = make_config(rules_file=None)
    default_file = target_dir / ".unclutter_rules.yaml"
    # Add a condition with invalid size value
    default_file.write_text(
        "- name: rule1\n  conditions:\n    larger: 100s\n  action:\n    type: move\n    target: /dest"
    )
    config.rules_file = str(default_file)
    mock_validate_rules_file.return_value = ["Invalid size value"]
    errors = validator.validate(config)
    assert any("Invalid size value" in e for e in errors)


def test_exceptions_handling(make_config, validator):
    config = make_config(rules_file="/some/path.yaml")
    with patch("pathlib.Path.exists", side_effect=MemoryError):
        with pytest.raises(MemoryError):
            validator.validate(config)

    with patch("pathlib.Path.exists", side_effect=PermissionError):
        with pytest.raises(PermissionError):
            validator.validate(config)

    with patch("pathlib.Path.exists", side_effect=OSError("os error")):
        with pytest.raises(OSError):
            validator.validate(config)

    with patch("pathlib.Path.exists", side_effect=ValueError("unexpected")):
        with pytest.raises(ValueError):
            validator.validate(config)
