import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from unclutter_directory.commands.delete_unpacked_command import DeleteUnpackedCommand
from unclutter_directory.comparison import ComparisonResult
from unclutter_directory.config.delete_unpacked_config import DeleteUnpackedConfig


@pytest.fixture
def temp_dir():
    """Fixture for temporary directory."""
    temp = tempfile.TemporaryDirectory()
    yield Path(temp.name)
    temp.cleanup()


@pytest.fixture
def mock_config(temp_dir):
    """Fixture for mock DeleteUnpackedConfig."""
    mock = Mock(spec=DeleteUnpackedConfig)
    mock.target_dir = temp_dir
    mock.quiet = False
    mock.dry_run = False
    mock.always_delete = False
    mock.never_delete = False
    mock.include_hidden = False
    return mock


@pytest.fixture
def mock_comparator():
    """Fixture for mocked ArchiveDirectoryComparator instance."""
    with patch(
        "unclutter_directory.commands.delete_unpacked_command.ArchiveDirectoryComparator"
    ) as mock_cls:
        mock_instance = Mock()
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_strategy():
    """Fixture for mocked delete strategy instance."""
    with patch(
        "unclutter_directory.commands.delete_unpacked_command.create_delete_strategy"
    ) as mock_create:
        mock_instance = Mock()
        mock_create.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_setup_logging():
    """Fixture for mocked setup_logging."""
    with patch(
        "unclutter_directory.commands.delete_unpacked_command.setup_logging"
    ) as mock:
        yield mock


@pytest.fixture
def mock_logger():
    """Fixture for mocked logger."""
    with patch("unclutter_directory.commands.delete_unpacked_command.logger") as mock:
        yield mock


@pytest.fixture
def identical_pair(temp_dir):
    """Fixture for creating an identical archive and unpacked directory pair."""
    # Generate unique name to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    dir_name = f"identical_{unique_id}"

    content1 = "This is file 1 content"
    content2 = "This is file 2 content"

    # Create temporary content directory
    content_dir = temp_dir / "temp_content"
    content_dir.mkdir()

    # Create files
    file1_path = content_dir / "file1.txt"
    file2_path = content_dir / "file2.txt"
    file1_path.write_text(content1)
    file2_path.write_text(content2)

    # Create ZIP archive
    archive_path = temp_dir / f"{dir_name}.zip"
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.write(file1_path, "file1.txt")
        zf.write(file2_path, "file2.txt")

    # Create unpacked directory with identical content
    unpacked_dir = temp_dir / dir_name
    unpacked_dir.mkdir()
    (unpacked_dir / "file1.txt").write_text(content1)
    (unpacked_dir / "file2.txt").write_text(content2)

    # Cleanup temp content
    shutil.rmtree(content_dir)

    yield archive_path, unpacked_dir

    # Cleanup after test
    if archive_path.exists():
        archive_path.unlink()
    if unpacked_dir.exists():
        shutil.rmtree(unpacked_dir)


def test_init(mock_config, mock_comparator, mock_strategy):
    """Test DeleteUnpackedCommand initialization."""
    command = DeleteUnpackedCommand(mock_config)

    # Verify attributes are set correctly
    assert command.config == mock_config
    assert command.comparator == mock_comparator
    assert command.delete_strategy == mock_strategy


@pytest.mark.parametrize("quiet", [False, True])
def test_execute_calls_setup_logging(
    mock_config, mock_setup_logging, mock_comparator, mock_strategy, mock_logger, quiet
):
    """Test that execute calls setup_logging with correct quiet value."""
    mock_config.quiet = quiet

    # Mock empty results to avoid complex execution
    mock_comparator.find_potential_duplicates.return_value = []

    command = DeleteUnpackedCommand(mock_config)
    command.execute()

    # Verify setup_logging was called with the correct quiet value
    mock_setup_logging.assert_called_once_with(quiet)


@pytest.fixture
def execute_scenario(request):
    """Indirect fixture for execute scenarios."""
    return request.param


@pytest.mark.parametrize(
    "execute_scenario",
    [
        {
            "name": "no_potential_duplicates",
            "pairs": [],
            "summary": {
                "identical": 0,
                "identical_percentage": 0.0,
                "different": 0,
            },
            "expect_compare": False,
            "expect_should_delete": False,
            "expect_perform": False,
            "expect_summary": False,
        },
        {
            "name": "potential_not_identical",
            "pairs": True,  # Flag to create mocks
            "identical": False,
            "differences": ["diff1", "diff2", "diff3", "diff4", "diff5", "diff6"],
            "summary": {
                "identical": 0,
                "identical_percentage": 0.0,
                "different": 1,
            },
            "expect_compare": True,
            "expect_should_delete": False,
            "expect_perform": False,
            "expect_summary": True,
        },
        {
            "name": "identical_should_delete",
            "pairs": True,
            "identical": True,
            "differences": [],
            "summary": {
                "identical": 1,
                "identical_percentage": 100.0,
                "different": 0,
            },
            "should_delete": True,
            "perform_return": True,
            "expect_compare": True,
            "expect_should_delete": True,
            "expect_perform": True,
            "expect_summary": True,
        },
        {
            "name": "identical_should_not_delete",
            "pairs": True,
            "identical": True,
            "differences": [],
            "summary": {
                "identical": 1,
                "identical_percentage": 100.0,
                "different": 0,
            },
            "should_delete": False,
            "expect_compare": True,
            "expect_should_delete": True,
            "expect_perform": False,
            "expect_summary": True,
        },
    ],
    indirect=True,
)
def test_execute_scenarios(
    mock_config, mock_comparator, mock_strategy, execute_scenario
):
    """Parametrized test for execute scenarios with potential duplicates."""
    scenario = execute_scenario

    # Setup find_potential_duplicates
    if scenario["pairs"] == []:
        mock_comparator.find_potential_duplicates.return_value = []
        archive_path = None
        directory_path = None
    elif scenario["pairs"]:
        # Create mock paths
        archive_path = Mock(spec=Path)
        archive_path.name = "test.zip"
        directory_path = Mock(spec=Path)
        directory_path.name = "test"
        mock_comparator.find_potential_duplicates.return_value = [
            (archive_path, directory_path)
        ]

        # Setup comparison result
        mock_result = ComparisonResult(
            archive_path=archive_path,
            directory_path=directory_path,
            identical=scenario["identical"],
            archive_files=[],
            directory_files=[],
            differences=scenario["differences"],
        )
        mock_comparator.compare_archive_and_directory.return_value = mock_result

    # Setup summary
    mock_comparator.get_comparison_summary.return_value = scenario["summary"]

    # Setup strategy if applicable
    if scenario.get("should_delete") is not None:
        mock_strategy.should_delete_directory.return_value = scenario["should_delete"]
    if scenario.get("perform_return") is not None:
        mock_strategy.perform_deletion.return_value = scenario["perform_return"]

    command = DeleteUnpackedCommand(mock_config)
    command.execute()

    # Verify find_potential_duplicates always called
    mock_comparator.find_potential_duplicates.assert_called_once_with(
        mock_config.target_dir
    )

    # Verify compare called if expected
    if scenario["expect_compare"]:
        mock_comparator.compare_archive_and_directory.assert_called_once_with(
            archive_path, directory_path
        )
    else:
        mock_comparator.compare_archive_and_directory.assert_not_called()

    # Verify strategy calls
    if scenario["expect_should_delete"]:
        mock_strategy.should_delete_directory.assert_called_once_with(
            directory_path, archive_path
        )
    else:
        mock_strategy.should_delete_directory.assert_not_called()

    if scenario["expect_perform"]:
        mock_strategy.perform_deletion.assert_called_once_with(
            directory_path, archive_path, False
        )
    else:
        mock_strategy.perform_deletion.assert_not_called()

    # Verify summary called if expected
    if scenario["expect_summary"]:
        mock_comparator.get_comparison_summary.assert_called_once()
    else:
        mock_comparator.get_comparison_summary.assert_not_called()


def test_execute_comparison_exception_handling(
    mock_config, mock_comparator, mock_strategy, mock_logger
):
    """Test execute handles exceptions during comparison gracefully."""
    # Mock archive and directory paths
    archive_path = Mock(spec=Path)
    archive_path.name = "test.zip"
    directory_path = Mock(spec=Path)
    directory_path.name = "test"

    # Mock one potential pair (but won't be used due to exception)
    mock_comparator.find_potential_duplicates.return_value = [
        (archive_path, directory_path)
    ]

    # Mock comparison to raise exception
    mock_comparator.compare_archive_and_directory.side_effect = Exception("Test error")
    mock_comparator.get_comparison_summary.return_value = {
        "identical": 0,
        "identical_percentage": 0.0,
        "different": 0,
    }

    command = DeleteUnpackedCommand(mock_config)
    command.execute()

    # Verify comparison was attempted
    mock_comparator.compare_archive_and_directory.assert_called_once_with(
        archive_path, directory_path
    )
    # Verify error was logged
    mock_logger.error.assert_called_once()
    # Verify execution continued despite error


def test_execute_keyboard_interrupt_handling(
    mock_config, mock_comparator, mock_strategy, mock_logger
):
    """Test execute handles KeyboardInterrupt gracefully."""
    # Mock find_potential_duplicates to raise KeyboardInterrupt
    mock_comparator.find_potential_duplicates.side_effect = KeyboardInterrupt()

    command = DeleteUnpackedCommand(mock_config)

    # Execute command - KeyboardInterrupt should be handled gracefully without re-raising
    command.execute()

    # Verify appropriate message was logged (KeyboardInterrupt handled without raising)
    mock_logger.info.assert_called_with("\n⏹️  Operation cancelled by user")


def test_execute_unexpected_exception_handling(
    mock_config, mock_comparator, mock_strategy, mock_logger
):
    """Test execute handles unexpected exceptions by re-raising."""
    # Mock one potential pair to trigger summary printing
    archive_path = Mock(spec=Path)
    archive_path.name = "test.zip"
    directory_path = Mock(spec=Path)
    directory_path.name = "test"

    mock_result = ComparisonResult(
        archive_path=archive_path,
        directory_path=directory_path,
        identical=False,
        archive_files=[],
        directory_files=[],
        differences=["diff1"],
    )

    mock_comparator.find_potential_duplicates.return_value = [
        (archive_path, directory_path)
    ]
    mock_comparator.compare_archive_and_directory.return_value = mock_result
    # Make get_comparison_summary raise the exception
    mock_comparator.get_comparison_summary.side_effect = Exception("Unexpected error")

    command = DeleteUnpackedCommand(mock_config)

    with pytest.raises(Exception) as context:
        command.execute()

    assert str(context.value) == "Unexpected error"
    # Verify error was logged
    mock_logger.error.assert_called_once_with(
        "❌ Unexpected error during check-duplicates operation: Unexpected error"
    )


def test_execute_calls_print_summary(mock_config, mock_comparator, mock_strategy):
    """Test execute calls _print_summary with correct parameters."""
    # Mock one potential pair to trigger summary printing
    archive_path = Mock(spec=Path)
    archive_path.name = "test.zip"
    directory_path = Mock(spec=Path)
    directory_path.name = "test"

    mock_result = ComparisonResult(
        archive_path=archive_path,
        directory_path=directory_path,
        identical=False,
        archive_files=[],
        directory_files=[],
        differences=["diff1"],
    )

    mock_comparator.find_potential_duplicates.return_value = [
        (archive_path, directory_path)
    ]
    mock_comparator.compare_archive_and_directory.return_value = mock_result
    mock_comparator.get_comparison_summary.return_value = {
        "identical": 0,
        "identical_percentage": 0.0,
        "different": 1,
    }

    command = DeleteUnpackedCommand(mock_config)
    command.execute()

    # Verify summary was printed
    mock_comparator.get_comparison_summary.assert_called_once()


def test_print_summary(mock_config, mock_logger):
    """Test _print_summary method."""
    # Create command instance (using fixtures for comparator and strategy, but not needed for _print_summary)
    with patch(
        "unclutter_directory.commands.delete_unpacked_command.ArchiveDirectoryComparator"
    ), patch(
        "unclutter_directory.commands.delete_unpacked_command.create_delete_strategy"
    ):
        command = DeleteUnpackedCommand(mock_config)

    # Create mock results
    mock_result1 = Mock(spec=ComparisonResult)
    mock_result2 = Mock(spec=ComparisonResult)
    results = [mock_result1, mock_result2]

    # Mock comparator summary
    command.comparator.get_comparison_summary.return_value = {
        "identical": 1,
        "identical_percentage": 50.0,
        "different": 1,
    }

    command._print_summary(results, 1, 2)

    # Verify summary logging calls
    mock_logger.info.assert_any_call("\n📊 Summary:")
    mock_logger.info.assert_any_call("   • Total pairs checked: 2")
    mock_logger.info.assert_any_call("   • Identical structures: 1 (50.0%)")


@pytest.fixture
def non_matching_pair(temp_dir):
    """Fixture for creating a non-matching archive and directory pair."""
    # Create archive
    archive_path = temp_dir / "test.zip"
    with open(archive_path, "wb") as f:
        with zipfile.ZipFile(f, "w") as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("file2.txt", "content2")

    # Create non-matching directory
    dir_path = temp_dir / "different_structure"
    dir_path.mkdir()
    (dir_path / "file_a.txt").write_text("different_content_a")
    (dir_path / "file_b.txt").write_text("different_content_b")
    (dir_path / "extra_file.txt").write_text("extra")  # Additional file

    yield archive_path, dir_path

    # Cleanup
    if archive_path.exists():
        archive_path.unlink()
    if dir_path.exists():
        shutil.rmtree(dir_path)


@pytest.fixture
def different_contents_pair(temp_dir):
    """Fixture for creating an archive and directory with different contents but matching name."""
    # Generate unique name to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    dir_name = f"test_{unique_id}"

    content1 = "This is file 1 content"
    content2 = "This is file 2 content"
    different_content1 = "Different content for file 1"

    # Create temporary content directory
    content_dir = temp_dir / "temp_content"
    content_dir.mkdir()

    # Create files
    file1_path = content_dir / "file1.txt"
    file2_path = content_dir / "file2.txt"
    file1_path.write_text(content1)
    file2_path.write_text(content2)

    # Create ZIP archive
    archive_path = temp_dir / f"{dir_name}.zip"
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.write(file1_path, "file1.txt")
        zf.write(file2_path, "file2.txt")

    # Create unpacked directory with different content
    unpacked_dir = temp_dir / dir_name
    unpacked_dir.mkdir()
    (unpacked_dir / "file1.txt").write_text(different_content1)
    (unpacked_dir / "file2.txt").write_text(content2)
    (unpacked_dir / "extra.txt").write_text("extra content")

    # Cleanup temp content
    shutil.rmtree(content_dir)

    yield archive_path, unpacked_dir

    # Cleanup after test
    if archive_path.exists():
        archive_path.unlink()
    if unpacked_dir.exists():
        shutil.rmtree(unpacked_dir)


@pytest.mark.parametrize(
    "mode,never_delete,always_delete,input_return",
    [
        ("dry_run", True, False, None),
        ("always_delete", False, True, None),
        ("interactive_yes", False, False, "y"),
        ("interactive_no", False, False, "n"),
    ],
)
def test_execute_identical_pair_modes_integration(
    temp_dir, identical_pair, mode, never_delete, always_delete, input_return
):
    """Parametrized test for identical pair with different deletion modes."""
    archive_path, unpacked_dir = identical_pair

    # Create config based on mode
    config = DeleteUnpackedConfig(
        target_dir=temp_dir,
        dry_run=False,  # Set explicitly
        always_delete=always_delete,
        never_delete=never_delete,
        include_hidden=False,
        quiet=True,
    )

    command = DeleteUnpackedCommand(config)

    # Patch input for interactive modes
    if input_return is not None:
        with patch("builtins.input", return_value=input_return):
            command.execute()
    else:
        command.execute()

    # Verify based on mode
    if mode == "always_delete" or mode == "interactive_yes":
        assert not unpacked_dir.exists()
    else:
        assert unpacked_dir.exists()


def test_execute_no_duplicates_integration(temp_dir, non_matching_pair):
    """Test execute with archive and non-matching directory - integration test."""
    archive_path, dir_path = non_matching_pair

    # Create config
    config = DeleteUnpackedConfig(
        target_dir=temp_dir,
        dry_run=True,  # Safe mode
        always_delete=False,
        never_delete=False,
        include_hidden=False,
        quiet=True,
    )

    command = DeleteUnpackedCommand(config)
    command.execute()

    # Verify directory still exists (no deletion occurred)
    assert dir_path.exists()


def test_execute_different_structures_integration(temp_dir, different_contents_pair):
    """Test execute with archive and directory having different contents."""
    archive_path, unpacked_dir = different_contents_pair

    # Create config
    config = DeleteUnpackedConfig(
        target_dir=temp_dir,
        dry_run=True,  # Safe mode
        always_delete=False,
        never_delete=False,
        include_hidden=False,
        quiet=True,
    )

    command = DeleteUnpackedCommand(config)
    with patch(
        "unclutter_directory.commands.delete_unpacked_command.logger"
    ) as mock_logger:
        command.execute()

    # Verify directory still exists (should not delete due to differences)
    assert unpacked_dir.exists()

    # Verify difference messages were logged
    difference_calls = [
        call
        for call in mock_logger.info.call_args_list
        if any(
            word in str(call).lower()
            for word in ["differs", "missing", "extra", "only in"]
        )
    ]
    assert len(difference_calls) > 0


@pytest.mark.parametrize("include_hidden", [False, True])
def test_execute_include_hidden_flag_integration(
    temp_dir, identical_pair, include_hidden
):
    """Parametrized test for --include-hidden flag affecting comparison results."""
    archive_path, unpacked_dir = identical_pair

    # Add a hidden file to the directory to create difference when include_hidden=True
    (unpacked_dir / ".hidden_file").write_text("hidden_content")

    config = DeleteUnpackedConfig(
        target_dir=temp_dir,
        dry_run=True,
        always_delete=False,
        never_delete=False,
        include_hidden=include_hidden,
        quiet=True,
    )

    command = DeleteUnpackedCommand(config)
    with patch(
        "unclutter_directory.commands.delete_unpacked_command.logger"
    ) as mock_logger:
        command.execute()

    # Directory should always exist due to dry_run
    assert unpacked_dir.exists()

    # Check for differences based on include_hidden
    difference_calls = [
        call
        for call in mock_logger.info.call_args_list
        if any(
            word in str(call).lower()
            for word in ["differs", "missing", "extra", "only in"]
        )
    ]
    if include_hidden:
        # Should report differences due to hidden file
        assert len(difference_calls) > 0
    else:
        # Should report as identical (ignoring hidden file), no differences
        assert len(difference_calls) == 0


def test_config_with_quiet_flag(temp_dir):
    """Test that DeleteUnpackedConfig handles quiet flag correctly."""
    config = DeleteUnpackedConfig(target_dir=temp_dir, quiet=True)

    assert config.quiet

    # Verify __str__ includes quiet flag
    str_repr = str(config)
    assert "quiet" in str_repr
