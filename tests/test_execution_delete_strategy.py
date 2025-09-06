from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest

from unclutter_directory.execution.delete_strategy import (
    AutomaticDeleteStrategy,
    DeleteConfirmationStrategy,
    DryRunDeleteStrategy,
    InteractiveDeleteStrategy,
    create_delete_strategy,
)


@pytest.fixture
def temp_paths():
    with TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        archive_path = temp_dir / "test.zip"
        directory_path = temp_dir / "test_dir"
        yield archive_path, directory_path


def test_abstract_methods():
    """Test that base class cannot be instantiated directly"""
    with pytest.raises(TypeError):
        DeleteConfirmationStrategy()


@pytest.fixture
def interactive_setup(temp_paths):
    archive_path, directory_path = temp_paths
    strategy = InteractiveDeleteStrategy()
    return strategy, directory_path, archive_path


@patch("unclutter_directory.execution.delete_strategy.logger")
@patch("builtins.input")
def test_should_delete_directory_yes_response(
    mock_input, mock_logger, interactive_setup
):
    """Test user responding 'y' to delete prompt"""
    strategy, directory_path, archive_path = interactive_setup
    mock_input.return_value = "y"

    result = strategy.should_delete_directory(directory_path, archive_path)

    assert result is True
    mock_input.assert_called_once()


@patch("unclutter_directory.execution.delete_strategy.logger")
@patch("builtins.input")
def test_should_delete_directory_no_response(
    mock_input, mock_logger, interactive_setup
):
    """Test user responding 'n' to delete prompt"""
    strategy, directory_path, archive_path = interactive_setup
    mock_input.return_value = "n"

    result = strategy.should_delete_directory(directory_path, archive_path)

    assert result is False
    mock_input.assert_called_once()


@patch("unclutter_directory.execution.delete_strategy.logger")
@patch("builtins.input")
def test_should_delete_directory_empty_response(
    mock_input, mock_logger, interactive_setup
):
    """Test user responding with empty string (defaults to no)"""
    strategy, directory_path, archive_path = interactive_setup
    mock_input.return_value = ""

    result = strategy.should_delete_directory(directory_path, archive_path)

    assert result is False


@patch("unclutter_directory.execution.delete_strategy.logger")
@patch("builtins.input")
def test_should_delete_directory_invalid_response_then_valid(
    mock_input, mock_logger, interactive_setup
):
    """Test invalid response followed by valid response"""
    strategy, directory_path, archive_path = interactive_setup
    mock_input.side_effect = ["invalid", "y"]

    result = strategy.should_delete_directory(directory_path, archive_path)

    assert result is True
    assert mock_input.call_count == 2


@patch("unclutter_directory.execution.delete_strategy.logger")
def test_should_delete_directory_keyboard_interrupt(mock_logger, interactive_setup):
    """Test handling KeyboardInterrupt during input"""
    strategy, directory_path, archive_path = interactive_setup
    with patch("builtins.input", side_effect=KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            strategy.should_delete_directory(directory_path, archive_path)


@patch("unclutter_directory.execution.delete_strategy.logger")
@patch("shutil.rmtree")
def test_perform_deletion_success(mock_rmtree, mock_logger, interactive_setup):
    """Test successful directory deletion"""
    strategy, directory_path, archive_path = interactive_setup
    mock_rmtree.return_value = None

    result = strategy.perform_deletion(directory_path, archive_path)

    assert result is True
    mock_rmtree.assert_called_once_with(directory_path)
    mock_logger.info.assert_called_once()


@patch("unclutter_directory.execution.delete_strategy.logger")
@patch("shutil.rmtree")
def test_perform_deletion_error(mock_rmtree, mock_logger, interactive_setup):
    """Test handling deletion failure"""
    strategy, directory_path, archive_path = interactive_setup
    mock_rmtree.side_effect = OSError("Permission denied")

    result = strategy.perform_deletion(directory_path, archive_path)

    assert result is False
    mock_logger.error.assert_called_once()


@patch("unclutter_directory.execution.delete_strategy.logger")
@patch("shutil.rmtree")
def test_perform_deletion_directory_not_exists(
    mock_rmtree, mock_logger, interactive_setup
):
    """Test deletion when directory doesn't exist"""
    strategy, directory_path, archive_path = interactive_setup
    mock_rmtree.side_effect = FileNotFoundError("No such file or directory")

    result = strategy.perform_deletion(directory_path, archive_path)

    assert result is False
    mock_logger.error.assert_called_once()


@patch("unclutter_directory.execution.delete_strategy.logger")
@patch("shutil.rmtree")
def test_perform_deletion_rmdir_error(mock_rmtree, mock_logger, interactive_setup):
    """Test handling rmtree failure (adapted from original rmdir)"""
    strategy, directory_path, archive_path = interactive_setup
    mock_rmtree.side_effect = OSError("Permission denied")

    result = strategy.perform_deletion(directory_path, archive_path)

    assert result is False
    mock_logger.error.assert_called_once()


@pytest.fixture
def auto_temp_paths():
    with TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        archive_path = temp_dir / "test.zip"
        directory_path = temp_dir / "test_dir"
        yield archive_path, directory_path


def test_should_delete_directory_always_delete_true_funcional(auto_temp_paths):
    """Test should_delete when always_delete is True"""
    archive_path, directory_path = auto_temp_paths
    strategy = AutomaticDeleteStrategy(always_delete=True)
    result = strategy.should_delete_directory(directory_path, archive_path)
    assert result is True


def test_should_delete_directory_never_execute_mode(auto_temp_paths):
    """Test should_delete when never_execute mode"""
    archive_path, directory_path = auto_temp_paths
    strategy = AutomaticDeleteStrategy(always_delete=False)
    result = strategy.should_delete_directory(directory_path, archive_path)
    assert result is False


def test_should_delete_directory_both_false(auto_temp_paths):
    """Test should_delete when both flags are False"""
    archive_path, directory_path = auto_temp_paths
    strategy = AutomaticDeleteStrategy()
    result = strategy.should_delete_directory(directory_path, archive_path)
    assert result is False


@pytest.fixture
def dry_temp_paths():
    with TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        archive_path = temp_dir / "test.zip"
        directory_path = temp_dir / "test_dir"
        yield archive_path, directory_path


def test_should_delete_directory_implementation(dry_temp_paths):
    """Test that should_delete_directory always returns False in dry run mode"""
    archive_path, directory_path = dry_temp_paths
    strategy = DryRunDeleteStrategy()
    result = strategy.should_delete_directory(directory_path, archive_path)
    assert result is False  # Dry run always returns False


@patch("unclutter_directory.execution.delete_strategy.logger")
def test_perform_deletion_dry_run_true(mock_logger, dry_temp_paths):
    """Test deletion in dry run mode"""
    archive_path, directory_path = dry_temp_paths
    strategy = DryRunDeleteStrategy()
    result = strategy.perform_deletion(directory_path, archive_path, dry_run=True)

    assert result is True  # Always returns True in dry run
    mock_logger.info.assert_called_once()


@patch("unclutter_directory.execution.delete_strategy.logger")
def test_perform_deletion_dry_run_false(mock_logger, dry_temp_paths):
    """Test deletion in normal mode (dry_run=False)"""
    archive_path, directory_path = dry_temp_paths
    strategy = DryRunDeleteStrategy()
    result = strategy.perform_deletion(directory_path, archive_path, dry_run=False)

    assert result is True  # Returns True even without actual deletion logic
    mock_logger.info.assert_called_once()


def test_create_interactive_strategy_default():
    """Test creating InteractiveDeleteStrategy by default"""
    strategy = create_delete_strategy()
    assert isinstance(strategy, InteractiveDeleteStrategy)


def test_create_interactive_strategy_explicit():
    """Test creating InteractiveDeleteStrategy explicitly"""
    strategy = create_delete_strategy(always_delete=False, never_delete=False)
    assert isinstance(strategy, InteractiveDeleteStrategy)


def test_create_dry_run_strategy():
    """Test creating DryRunDeleteStrategy"""
    strategy = create_delete_strategy(never_delete=True)
    assert isinstance(strategy, DryRunDeleteStrategy)


@pytest.fixture
def create_temp_paths():
    with TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        archive_path = temp_dir / "test.zip"
        directory_path = temp_dir / "test_dir"
        yield directory_path, archive_path


def test_create_automatic_strategy_always_delete(create_temp_paths):
    """Test creating AutomaticDeleteStrategy with always_delete"""
    directory_path, archive_path = create_temp_paths
    strategy = create_delete_strategy(always_delete=True, never_delete=False)
    assert isinstance(strategy, AutomaticDeleteStrategy)
    # Test that it behaves correctly with always_delete=True
    result = strategy.should_delete_directory(directory_path, archive_path)
    assert result is True


def test_create_automatic_strategy_never_delete():
    """Test creating DryRunDeleteStrategy when never_delete is True"""
    strategy = create_delete_strategy(always_delete=False, never_delete=True)
    assert isinstance(strategy, DryRunDeleteStrategy)


def test_create_automatic_strategy_both_flags():
    """Test creating DryRunDeleteStrategy when never_delete overrides always_delete"""
    strategy = create_delete_strategy(always_delete=True, never_delete=True)
    assert isinstance(strategy, DryRunDeleteStrategy)
