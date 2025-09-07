import tempfile
import textwrap
from pathlib import Path
from unittest.mock import Mock, call, patch
from zipfile import ZipFile

import pytest

from unclutter_directory.commands.organize_command import OrganizeCommand
from unclutter_directory.config.organize_config import OrganizeConfig
from unclutter_directory.factories.component_factory import ComponentFactory
from unclutter_directory.validation.validation_chain import ValidationChain


@pytest.fixture
def temp_path():
    with tempfile.TemporaryDirectory() as temp_dir_name:
        yield Path(temp_dir_name)


@pytest.fixture
def mock_config(temp_path):
    mock = Mock(spec=OrganizeConfig)
    mock.target_dir = temp_path
    mock.rules_file_path = temp_path / "rules.yaml"
    mock.dry_run = False
    mock.quiet = False
    return mock


@pytest.fixture
def mock_factory():
    mock_matcher = Mock()
    mock_collector = Mock()
    mock_strategy = Mock()
    mock_factory = Mock()
    mock_factory.create_file_matcher.return_value = mock_matcher
    mock_factory.create_file_collector.return_value = mock_collector
    mock_factory.create_execution_strategy.return_value = mock_strategy
    return mock_factory


@pytest.fixture
def mock_processor():
    return Mock()


@pytest.fixture
def source_dir(temp_path):
    source_dir = temp_path / "source"
    source_dir.mkdir()
    return source_dir


def test_init(mock_config):
    """Test OrganizeCommand initialization"""
    command = OrganizeCommand(mock_config)

    # Verify attributes are set correctly
    assert command.config == mock_config
    assert isinstance(command.validation_chain, ValidationChain)
    assert isinstance(command.factory, ComponentFactory)
    assert command.rule_responses == {}


@pytest.mark.parametrize(
    "quiet, expected",
    [
        (True, True),
        (False, False),
    ],
)
@patch("unclutter_directory.commands.organize_command.setup_logging")
def test_setup_logging(mock_setup_logging, mock_config, quiet, expected):
    """Test logging setup for quiet and verbose modes"""
    mock_config.quiet = quiet

    command = OrganizeCommand(mock_config)
    command._setup_logging()

    mock_setup_logging.assert_called_once_with(expected)


@patch("unclutter_directory.commands.organize_command.ValidationChain")
@patch("unclutter_directory.commands.organize_command.sys.exit")
def test_validate_config_no_errors(mock_exit, mock_validation_chain_cls, mock_config):
    """Test validation with no errors"""
    # Setup mock validation chain
    mock_validation_chain = Mock()
    mock_validation_chain.validate.return_value = []
    mock_validation_chain_cls.return_value = mock_validation_chain

    command = OrganizeCommand(mock_config)
    command._validate_config()

    # Verify validate was called and exit was not called
    mock_validation_chain.validate.assert_called_once_with(mock_config)
    mock_exit.assert_not_called()


@patch("unclutter_directory.commands.organize_command.logger")
@patch("unclutter_directory.commands.organize_command.ValidationChain")
@patch("unclutter_directory.commands.organize_command.sys.exit")
def test_validate_config_with_errors(
    mock_exit, mock_validation_chain_cls, mock_logger, mock_config
):
    """Test validation with errors"""
    # Setup mock validation chain with errors
    mock_validation_chain = Mock()
    mock_validation_chain.validate.return_value = ["Error 1", "Error 2"]
    mock_validation_chain_cls.return_value = mock_validation_chain

    command = OrganizeCommand(mock_config)
    command._validate_config()

    # Verify validate was called
    mock_validation_chain.validate.assert_called_once_with(mock_config)

    # Verify error logging with correct calls
    expected_calls = [
        call("Configuration validation failed:"),
        call("  • Error 1"),
        call("  • Error 2"),
    ]
    assert mock_logger.error.call_args_list == expected_calls

    # Verify exit was called with code 1
    mock_exit.assert_called_once_with(1)


@patch("unclutter_directory.commands.organize_command.logger")
@patch("unclutter_directory.commands.organize_command.FileProcessor")
@patch("unclutter_directory.commands.organize_command.ComponentFactory")
def test_process_files_no_files_found(
    mock_factory_cls, mock_processor_cls, mock_logger, mock_config, mock_factory
):
    """Test processing when no files are found"""
    mock_factory_cls.return_value = mock_factory

    # Setup collector to return empty list
    mock_collector = mock_factory.create_file_collector.return_value
    mock_collector.collect.return_value = []

    command = OrganizeCommand(mock_config)
    command._process_files()

    # Verify collector was called
    mock_collector.collect.assert_called_once_with(mock_config.target_dir)

    # Verify no processing occurred
    mock_processor_cls.assert_not_called()
    mock_logger.info.assert_called_once_with("No files found to process")


@patch("unclutter_directory.commands.organize_command.logger")
@patch("unclutter_directory.commands.organize_command.FileProcessor")
@patch("unclutter_directory.commands.organize_command.ComponentFactory")
def test_process_files_successful_processing(
    mock_factory_cls,
    mock_processor_cls,
    mock_logger,
    mock_config,
    mock_factory,
    mock_processor,
):
    """Test successful file processing"""
    mock_factory_cls.return_value = mock_factory
    mock_processor_cls.return_value = mock_processor

    # Setup collector to return files
    test_files = [
        mock_config.target_dir / "file1.txt",
        mock_config.target_dir / "file2.txt",
    ]
    mock_collector = mock_factory.create_file_collector.return_value
    mock_collector.collect.return_value = test_files

    # Setup processor with stats
    test_stats = {
        "total_files": 2,
        "processed_files": 2,
        "skipped_files": 0,
        "errors": 0,
    }
    mock_processor.process_files.return_value = test_stats

    command = OrganizeCommand(mock_config)
    command._process_files()

    # Verify all components were created
    mock_factory.create_file_matcher.assert_called_once_with(mock_config)
    mock_factory.create_file_collector.assert_called_once_with(mock_config)
    mock_factory.create_execution_strategy.assert_called_once_with(mock_config)

    # Verify processor was created and called
    mock_matcher = mock_factory.create_file_matcher.return_value
    mock_strategy = mock_factory.create_execution_strategy.return_value
    mock_processor_cls.assert_called_once_with(
        mock_matcher, mock_strategy, command.rule_responses, mock_config
    )
    mock_processor.process_files.assert_called_once_with(
        test_files, mock_config.target_dir
    )

    # Verify summary logging was called
    assert mock_logger.info.called


@pytest.mark.parametrize(
    "dry_run, processed_files, errors, expected_info, expected_warning",
    [
        (
            True,
            8,
            0,
            [
                "Dry run completed: 8/10 files would be processed",
                "  • 2 files skipped (no matching rules)",
            ],
            None,
        ),
        (
            False,
            7,
            1,
            [
                "Processing completed: 7/10 files processed",
                "  • 2 files skipped (no matching rules)",
            ],
            "  • 1 files had errors during processing",
        ),
    ],
)
@patch("unclutter_directory.commands.organize_command.logger")
def test_log_processing_summary(
    mock_logger,
    mock_config,
    dry_run,
    processed_files,
    errors,
    expected_info,
    expected_warning,
):
    """Test logging summary for dry run and normal modes"""
    mock_config.dry_run = dry_run

    command = OrganizeCommand(mock_config)

    # Test stats
    stats = {
        "total_files": 10,
        "processed_files": processed_files,
        "skipped_files": 2,
        "errors": errors,
    }

    command._log_processing_summary(stats)

    # Verify info calls
    assert mock_logger.info.call_args_list == [call(msg) for msg in expected_info]

    if expected_warning is not None:
        mock_logger.warning.assert_called_once_with(expected_warning)
    else:
        mock_logger.warning.assert_not_called()


@patch.object(OrganizeCommand, "_process_files")
@patch.object(OrganizeCommand, "_validate_config")
@patch.object(OrganizeCommand, "_setup_logging")
def test_execute_successful_flow(
    mock_setup_logging, mock_validate_config, mock_process_files, mock_config
):
    """Test successful execution flow"""
    command = OrganizeCommand(mock_config)
    command.execute()

    # Verify all steps were called in correct order
    mock_setup_logging.assert_called_once()
    mock_validate_config.assert_called_once()
    mock_process_files.assert_called_once()


@patch("unclutter_directory.commands.organize_command.logger")
@patch.object(OrganizeCommand, "_setup_logging")
def test_execute_keyboard_interrupt(mock_setup_logging, mock_logger, mock_config):
    """Test execution with KeyboardInterrupt"""
    command = OrganizeCommand(mock_config)

    # Make _validate_config raise KeyboardInterrupt
    with patch.object(command, "_validate_config", side_effect=KeyboardInterrupt()):
        command.execute()

    # Verify interrupt was handled
    mock_logger.info.assert_called_once_with("\nOperation cancelled by user")


@patch("unclutter_directory.commands.organize_command.logger")
@patch.object(OrganizeCommand, "_setup_logging")
def test_execute_generic_exception(mock_setup_logging, mock_logger, mock_config):
    """Test execution with generic exception"""
    command = OrganizeCommand(mock_config)

    # Make _validate_config raise generic exception
    test_exception = ValueError("Test error")
    with patch.object(command, "_validate_config", side_effect=test_exception):
        with pytest.raises(ValueError):
            command.execute()

    # Verify error was logged
    mock_logger.error.assert_called_once_with(
        f"Unexpected error during organize operation: {test_exception}"
    )


def test_organize_with_delete_unpacked_always_delete(temp_path, caplog):
    """Test organize command with delete_unpacked_on_match and always_delete flag"""
    caplog.set_level(0)  # Capture all logs
    # Use temp_path as the working directory where files are created and processed
    target_dir = temp_path

    # Create unpacked directory
    unpacked_dir = target_dir / "test"
    unpacked_dir.mkdir()
    (unpacked_dir / "file1.txt").write_text("content")
    (unpacked_dir / "file2.txt").write_text("content")

    # Create zip archive with same content
    zip_path = target_dir / "test.zip"
    with ZipFile(zip_path, "w") as z:
        for f in unpacked_dir.iterdir():
            z.write(str(f), f.name)

    assert zip_path.exists()

    # Create rules file
    rules_file = target_dir / "rules.yaml"
    rules_file.write_text(
        textwrap.dedent("""
- name: "Test rule"
  conditions:
    end: ".zip"
  action:
    type: move
    target: "archives"
  delete_unpacked_on_match: true
""")
    )

    # Create config
    config = OrganizeConfig(
        target_dir=target_dir,
        rules_file=str(rules_file),
        dry_run=False,
        always_delete=True,
        quiet=False,
        never_delete=False,
        include_hidden=False,
    )

    # Execute command
    command = OrganizeCommand(config)
    command.execute()

    # Assert zip was moved
    expected_zip = target_dir / "archives" / "test.zip"
    assert expected_zip.exists()
    assert not zip_path.exists()

    # Assert unpacked directory was deleted
    assert not unpacked_dir.exists()

    # Assert logs for cleaning
    assert "Cleaning unpacked directory for preexisting archive" in caplog.text


def test_organize_with_delete_unpacked_dry_run(temp_path, caplog):
    """Test organize command with delete_unpacked_on_match in dry-run mode"""
    caplog.set_level(0)  # Capture all logs
    # Use temp_path as the working directory where files are created and processed
    target_dir = temp_path

    # Create unpacked directory
    unpacked_dir = target_dir / "test"
    unpacked_dir.mkdir()
    (unpacked_dir / "file1.txt").write_text("content")
    (unpacked_dir / "file2.txt").write_text("content")

    # Create zip archive with same content
    zip_path = target_dir / "test.zip"
    with ZipFile(zip_path, "w") as z:
        for f in unpacked_dir.iterdir():
            z.write(str(f), f.name)

    assert zip_path.exists()

    # Create rules file
    rules_file = target_dir / "rules.yaml"
    rules_file.write_text(
        textwrap.dedent("""
- name: "Test rule"
  conditions:
    end: ".zip"
  action:
    type: move
    target: "archives"
  delete_unpacked_on_match: true
""")
    )

    # Create config with dry_run
    config = OrganizeConfig(
        target_dir=target_dir,
        rules_file=str(rules_file),
        dry_run=True,
        always_delete=False,
        quiet=False,
        never_delete=False,
        include_hidden=False,
    )

    # Execute command
    command = OrganizeCommand(config)
    command.execute()

    # Assert nothing was moved or deleted
    assert zip_path.exists()
    assert unpacked_dir.exists()

    # Assert logs indicate planned actions but no execution
    assert "[DRY RUN] Would execute" in caplog.text
    assert "Cleaning unpacked directory" not in caplog.text
