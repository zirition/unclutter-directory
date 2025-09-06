import tempfile
from pathlib import Path

import pytest

from unclutter_directory.config.organize_config import ExecutionMode, OrganizeConfig


@pytest.fixture
def temp_dir():
    """Set up test environment with temporary directory"""
    with tempfile.TemporaryDirectory() as temp_path:
        yield Path(temp_path)


def test_valid_config_creation(temp_dir):
    """Test creation of valid configuration"""
    config = OrganizeConfig(
        target_dir=temp_dir,
        rules_file="rules.yaml",
        dry_run=False,
        quiet=False,
        always_delete=False,
        never_delete=False,
        include_hidden=False,
    )

    assert config.target_dir == temp_dir
    assert config.rules_file == "rules.yaml"
    assert not config.dry_run
    assert not config.quiet
    assert not config.always_delete
    assert not config.never_delete
    assert not config.include_hidden


def test_mutually_exclusive_flags_validation_error(temp_dir):
    """Test that ValueError is raised when always_delete and never_delete are both True"""
    with pytest.raises(ValueError) as context:
        OrganizeConfig(
            target_dir=temp_dir,
            rules_file=None,
            dry_run=False,
            quiet=False,
            always_delete=True,
            never_delete=True,
            include_hidden=False,
        )

    assert "always_delete and never_delete are mutually exclusive" in str(context.value)


@pytest.mark.parametrize(
    "dry_run, always_delete, never_delete, expected_mode",
    [
        (True, False, False, ExecutionMode.DRY_RUN),  # dry_run case
        (False, True, False, ExecutionMode.AUTOMATIC),  # always_delete
        (False, False, True, ExecutionMode.AUTOMATIC),  # never_delete
        (False, False, False, ExecutionMode.INTERACTIVE),  # default
        (True, True, False, ExecutionMode.DRY_RUN),  # overrides with dry_run
    ],
    ids=[
        "dry_run_true",
        "always_delete_true",
        "never_delete_true",
        "interactive_default",
        "dry_run_overrides_always_delete",
    ],
)
def test_execution_mode(temp_dir, dry_run, always_delete, never_delete, expected_mode):
    """Test execution_mode property for various flag combinations"""
    config = OrganizeConfig(
        target_dir=temp_dir,
        rules_file=None,
        dry_run=dry_run,
        quiet=False,
        always_delete=always_delete,
        never_delete=never_delete,
        include_hidden=False,
    )

    assert config.execution_mode == expected_mode


@pytest.mark.parametrize(
    "rules_file, expected",
    [
        ("custom_rules.yaml", Path("custom_rules.yaml")),
        (None, None),
    ],
    ids=["valid_path", "none"],
)
def test_rules_file_path(temp_dir, rules_file, expected):
    """Test rules_file_path property for different rules_file values"""
    config = OrganizeConfig(
        target_dir=temp_dir,
        rules_file=rules_file,
        dry_run=False,
        quiet=False,
        always_delete=False,
        never_delete=False,
        include_hidden=False,
    )

    assert config.rules_file_path == expected


@pytest.mark.parametrize(
    "target_dir_input, expected_target_dir",
    [
        (Path("/some/path"), Path("/some/path")),
        (
            "/another/path",
            "/another/path",
        ),  # Assuming it remains str; adjust if converted
    ],
    ids=["path_object", "string_path"],
)
def test_config_with_various_target_dir_types(
    target_dir_input, expected_target_dir, temp_dir
):
    """Test configuration creation with different types of target_dir"""
    config = OrganizeConfig(
        target_dir=target_dir_input,
        rules_file=None,
        dry_run=False,
        quiet=False,
        always_delete=False,
        never_delete=False,
        include_hidden=False,
    )
    if isinstance(expected_target_dir, str):
        assert str(config.target_dir) == expected_target_dir
    else:
        assert config.target_dir == expected_target_dir
