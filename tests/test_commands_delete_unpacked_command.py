import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

from unclutter_directory.commands.delete_unpacked_command import DeleteUnpackedCommand
from unclutter_directory.config.delete_unpacked_config import DeleteUnpackedConfig


class TestDeleteUnpackedCommand(unittest.TestCase):
    """
    Unit tests for DeleteUnpackedCommand class
    """

    def setUp(self):
        """Set up test environment with temporary directory"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.temp_dir.name)

        # Create mock config with required attributes
        self.mock_config = Mock(spec=DeleteUnpackedConfig)
        self.mock_config.target_dir = self.test_path
        self.mock_config.quiet = False
        self.mock_config.dry_run = False
        self.mock_config.always_delete = False
        self.mock_config.never_delete = False
        self.mock_config.include_hidden = False

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    @patch(
        "unclutter_directory.commands.delete_unpacked_command.ArchiveDirectoryComparator"
    )
    @patch(
        "unclutter_directory.commands.delete_unpacked_command.create_delete_strategy"
    )
    def test_init(self, mock_create_strategy, mock_comparator_cls):
        """Test DeleteUnpackedCommand initialization"""
        # Mock comparator instance
        mock_comparator = Mock()
        mock_comparator_cls.return_value = mock_comparator

        # Mock strategy instance
        mock_strategy = Mock()
        mock_create_strategy.return_value = mock_strategy

        command = DeleteUnpackedCommand(self.mock_config)

        # Verify attributes are set correctly
        self.assertEqual(command.config, self.mock_config)
        self.assertEqual(command.comparator, mock_comparator)
        self.assertEqual(command.delete_strategy, mock_strategy)

    @patch("unclutter_directory.commands.delete_unpacked_command.setup_logging")
    @patch(
        "unclutter_directory.commands.delete_unpacked_command.create_delete_strategy"
    )
    @patch(
        "unclutter_directory.commands.delete_unpacked_command.ArchiveDirectoryComparator"
    )
    @patch("unclutter_directory.commands.delete_unpacked_command.logger")
    def test_execute_calls_setup_logging_quiet_false(
        self, mock_logger, mock_comparator_cls, mock_create_strategy, mock_setup_logging
    ):
        """Test that execute calls setup_logging with correct quiet value"""
        self.mock_config.quiet = False

        # Mock dependencies
        mock_comparator = Mock()
        mock_comparator_cls.return_value = mock_comparator
        mock_strategy = Mock()
        mock_create_strategy.return_value = mock_strategy

        # Mock empty results to avoid complex execution
        mock_comparator.find_potential_duplicates.return_value = []

        command = DeleteUnpackedCommand(self.mock_config)
        command.execute()

        # Verify setup_logging was called with False
        mock_setup_logging.assert_called_once_with(False)

    @patch("unclutter_directory.commands.delete_unpacked_command.setup_logging")
    @patch(
        "unclutter_directory.commands.delete_unpacked_command.create_delete_strategy"
    )
    @patch(
        "unclutter_directory.commands.delete_unpacked_command.ArchiveDirectoryComparator"
    )
    @patch("unclutter_directory.commands.delete_unpacked_command.logger")
    def test_execute_calls_setup_logging_quiet_true(
        self, mock_logger, mock_comparator_cls, mock_create_strategy, mock_setup_logging
    ):
        """Test that execute calls setup_logging with correct quiet value when True"""
        self.mock_config.quiet = True

        # Mock dependencies
        mock_comparator = Mock()
        mock_comparator_cls.return_value = mock_comparator
        mock_strategy = Mock()
        mock_create_strategy.return_value = mock_strategy

        # Mock empty results to avoid complex execution
        mock_comparator.find_potential_duplicates.return_value = []

        command = DeleteUnpackedCommand(self.mock_config)
        command.execute()

        # Verify setup_logging was called with True
        mock_setup_logging.assert_called_once_with(True)

    def test_execute_no_potential_duplicates(self):
        """Test execute when no potential duplicates are found"""
        with patch(
            "unclutter_directory.commands.delete_unpacked_command.ArchiveDirectoryComparator"
        ) as mock_comparator_cls, patch(
            "unclutter_directory.commands.delete_unpacked_command.create_delete_strategy"
        ) as mock_create_strategy:
            # Mock dependencies
            mock_comparator = Mock()
            mock_comparator_cls.return_value = mock_comparator
            mock_strategy = Mock()
            mock_create_strategy.return_value = mock_strategy

            # Mock empty results
            mock_comparator.find_potential_duplicates = Mock(return_value=[])

            command = DeleteUnpackedCommand(self.mock_config)
            command.execute()

            # Verify find_potential_duplicates was called
            mock_comparator.find_potential_duplicates.assert_called_once_with(
                self.mock_config.target_dir
            )
            # Verify no comparison or deletion calls
            mock_comparator.compare_archive_and_directory.assert_not_called()
            mock_strategy.should_delete_directory.assert_not_called()
            mock_strategy.perform_deletion.assert_not_called()

    def test_execute_potential_duplicates_not_identical(self):
        """Test execute with potential duplicates that are not identical"""
        with patch(
            "unclutter_directory.commands.delete_unpacked_command.ArchiveDirectoryComparator"
        ) as mock_comparator_cls, patch(
            "unclutter_directory.commands.delete_unpacked_command.create_delete_strategy"
        ) as mock_create_strategy:
            # Mock dependencies
            mock_comparator = Mock()
            mock_comparator_cls.return_value = mock_comparator
            mock_strategy = Mock()
            mock_create_strategy.return_value = mock_strategy

            # Mock archive and directory paths
            archive_path = Mock(spec=Path)
            archive_path.name = "test.zip"
            directory_path = Mock(spec=Path)
            directory_path.name = "test"

            # Mock one potential pair
            mock_comparator.find_potential_duplicates = Mock(
                return_value=[(archive_path, directory_path)]
            )

            # Mock comparison result - not identical
            from unclutter_directory.comparison import ComparisonResult

            mock_result = ComparisonResult(
                archive_path=archive_path,
                directory_path=directory_path,
                identical=False,
                archive_files=[],
                directory_files=[],
                differences=["diff1", "diff2", "diff3", "diff4", "diff5", "diff6"],
            )
            mock_comparator.compare_archive_and_directory.return_value = mock_result
            mock_comparator.get_comparison_summary.return_value = {
                "identical": 0,
                "identical_percentage": 0.0,
                "different": 1,
            }

            command = DeleteUnpackedCommand(self.mock_config)
            command.execute()

            # Verify comparison was called
            mock_comparator.compare_archive_and_directory.assert_called_once_with(
                archive_path, directory_path
            )
            # Verify no deletion calls since not identical
            mock_strategy.should_delete_directory.assert_not_called()
            mock_strategy.perform_deletion.assert_not_called()

    def test_execute_potential_duplicates_identical_should_delete(self):
        """Test execute with identical duplicates that should be deleted"""
        with patch(
            "unclutter_directory.commands.delete_unpacked_command.ArchiveDirectoryComparator"
        ) as mock_comparator_cls, patch(
            "unclutter_directory.commands.delete_unpacked_command.create_delete_strategy"
        ) as mock_create_strategy:
            # Mock dependencies
            mock_comparator = Mock()
            mock_comparator_cls.return_value = mock_comparator
            mock_strategy = Mock()
            mock_create_strategy.return_value = mock_strategy

            # Mock archive and directory paths
            archive_path = Mock(spec=Path)
            archive_path.name = "test.zip"
            directory_path = Mock(spec=Path)
            directory_path.name = "test"

            # Mock one potential pair
            mock_comparator.find_potential_duplicates = Mock(
                return_value=[(archive_path, directory_path)]
            )

            # Mock comparison result - identical
            from unclutter_directory.comparison import ComparisonResult

            mock_result = ComparisonResult(
                archive_path=archive_path,
                directory_path=directory_path,
                identical=True,
                archive_files=[],
                directory_files=[],
                differences=[],
            )
            mock_comparator.compare_archive_and_directory.return_value = mock_result
            mock_comparator.get_comparison_summary.return_value = {
                "identical": 1,
                "identical_percentage": 100.0,
                "different": 0,
            }

            # Mock strategy responses
            mock_strategy.should_delete_directory.return_value = True
            mock_strategy.perform_deletion.return_value = True

            command = DeleteUnpackedCommand(self.mock_config)
            command.execute()

            # Verify comparison was called
            mock_comparator.compare_archive_and_directory.assert_called_once_with(
                archive_path, directory_path
            )
            # Verify deletion decisions
            mock_strategy.should_delete_directory.assert_called_once_with(
                directory_path, archive_path
            )
            mock_strategy.perform_deletion.assert_called_once_with(
                directory_path, archive_path, False
            )

    def test_execute_potential_duplicates_identical_should_not_delete(self):
        """Test execute with identical duplicates that should not be deleted"""
        with patch(
            "unclutter_directory.commands.delete_unpacked_command.ArchiveDirectoryComparator"
        ) as mock_comparator_cls, patch(
            "unclutter_directory.commands.delete_unpacked_command.create_delete_strategy"
        ) as mock_create_strategy:
            # Mock dependencies
            mock_comparator = Mock()
            mock_comparator_cls.return_value = mock_comparator
            mock_strategy = Mock()
            mock_create_strategy.return_value = mock_strategy

            # Mock archive and directory paths
            archive_path = Mock(spec=Path)
            archive_path.name = "test.zip"
            directory_path = Mock(spec=Path)
            directory_path.name = "test"

            # Mock one potential pair
            mock_comparator.find_potential_duplicates = Mock(
                return_value=[(archive_path, directory_path)]
            )

            # Mock comparison result - identical
            from unclutter_directory.comparison import ComparisonResult

            mock_result = ComparisonResult(
                archive_path=archive_path,
                directory_path=directory_path,
                identical=True,
                archive_files=[],
                directory_files=[],
                differences=[],
            )
            mock_comparator.compare_archive_and_directory.return_value = mock_result
            mock_comparator.get_comparison_summary.return_value = {
                "identical": 1,
                "identical_percentage": 100.0,
                "different": 0,
            }

            # Mock strategy responses
            mock_strategy.should_delete_directory.return_value = False

            command = DeleteUnpackedCommand(self.mock_config)
            command.execute()

            # Verify comparison was called
            mock_comparator.compare_archive_and_directory.assert_called_once_with(
                archive_path, directory_path
            )
            # Verify should_delete_directory was called but not perform_deletion
            mock_strategy.should_delete_directory.assert_called_once_with(
                directory_path, archive_path
            )
            mock_strategy.perform_deletion.assert_not_called()

    def test_execute_comparison_exception_handling(self):
        """Test execute handles exceptions during comparison gracefully"""
        with patch(
            "unclutter_directory.commands.delete_unpacked_command.ArchiveDirectoryComparator"
        ) as mock_comparator_cls, patch(
            "unclutter_directory.commands.delete_unpacked_command.create_delete_strategy"
        ) as mock_create_strategy, patch(
            "unclutter_directory.commands.delete_unpacked_command.logger"
        ) as mock_logger:
            # Mock dependencies
            mock_comparator = Mock()
            mock_comparator_cls.return_value = mock_comparator
            mock_strategy = Mock()
            mock_create_strategy.return_value = mock_strategy

            # Mock archive and directory paths
            archive_path = Mock(spec=Path)
            archive_path.name = "test.zip"
            directory_path = Mock(spec=Path)
            directory_path.name = "test"

            # Mock one potential pair (but won't be used due to exception)
            mock_comparator.find_potential_duplicates = Mock(
                return_value=[(archive_path, directory_path)]
            )

            # Mock comparison to raise exception
            mock_comparator.compare_archive_and_directory.side_effect = Exception(
                "Test error"
            )
            mock_comparator.get_comparison_summary.return_value = {
                "identical": 0,
                "identical_percentage": 0.0,
                "different": 0,
            }

            command = DeleteUnpackedCommand(self.mock_config)
            command.execute()

            # Verify comparison was attempted
            mock_comparator.compare_archive_and_directory.assert_called_once_with(
                archive_path, directory_path
            )
            # Verify error was logged
            mock_logger.error.assert_called_once()
            # Verify execution continued despite error
            self.assertTrue(mock_logger.error.called)

    def test_execute_keyboard_interrupt_handling(self):
        """Test execute handles KeyboardInterrupt gracefully"""
        with patch(
            "unclutter_directory.commands.delete_unpacked_command.ArchiveDirectoryComparator"
        ) as mock_comparator_cls, patch(
            "unclutter_directory.commands.delete_unpacked_command.create_delete_strategy"
        ) as mock_create_strategy, patch(
            "unclutter_directory.commands.delete_unpacked_command.logger"
        ) as mock_logger:
            # Mock dependencies
            mock_comparator = Mock()
            mock_comparator_cls.return_value = mock_comparator
            mock_strategy = Mock()
            mock_create_strategy.return_value = mock_strategy

            # Mock find_potential_duplicates to raise KeyboardInterrupt
            mock_comparator.find_potential_duplicates.side_effect = KeyboardInterrupt()

            command = DeleteUnpackedCommand(self.mock_config)

            # Execute command - KeyboardInterrupt should be handled gracefully without re-raising
            command.execute()

            # Verify appropriate message was logged (KeyboardInterrupt handled without raising)
            mock_logger.info.assert_called_with("\n⏹️  Operation cancelled by user")

    def test_execute_unexpected_exception_handling(self):
        """Test execute handles unexpected exceptions by re-raising"""
        with patch(
            "unclutter_directory.commands.delete_unpacked_command.ArchiveDirectoryComparator"
        ) as mock_comparator_cls, patch(
            "unclutter_directory.commands.delete_unpacked_command.create_delete_strategy"
        ) as mock_create_strategy, patch(
            "unclutter_directory.commands.delete_unpacked_command.logger"
        ) as mock_logger:
            # Mock dependencies
            mock_comparator = Mock()
            mock_comparator_cls.return_value = mock_comparator
            mock_strategy = Mock()
            mock_create_strategy.return_value = mock_strategy

            # Mock one potential pair to trigger summary printing
            archive_path = Mock(spec=Path)
            archive_path.name = "test.zip"
            directory_path = Mock(spec=Path)
            directory_path.name = "test"

            from unclutter_directory.comparison import ComparisonResult

            mock_result = ComparisonResult(
                archive_path=archive_path,
                directory_path=directory_path,
                identical=False,
                archive_files=[],
                directory_files=[],
                differences=["diff1"],
            )

            mock_comparator.find_potential_duplicates = Mock(
                return_value=[(archive_path, directory_path)]
            )
            mock_comparator.compare_archive_and_directory.return_value = mock_result
            # Make get_comparison_summary raise the exception
            mock_comparator.get_comparison_summary.side_effect = Exception(
                "Unexpected error"
            )

            command = DeleteUnpackedCommand(self.mock_config)

            with self.assertRaises(Exception) as context:
                command.execute()

            self.assertEqual(str(context.exception), "Unexpected error")
            # Verify error was logged
            mock_logger.error.assert_called_once_with(
                "❌ Unexpected error during check-duplicates operation: Unexpected error"
            )

    def test_execute_calls_print_summary(self):
        """Test execute calls _print_summary with correct parameters"""
        with patch(
            "unclutter_directory.commands.delete_unpacked_command.ArchiveDirectoryComparator"
        ) as mock_comparator_cls, patch(
            "unclutter_directory.commands.delete_unpacked_command.create_delete_strategy"
        ) as mock_create_strategy:
            # Mock dependencies
            mock_comparator = Mock()
            mock_comparator_cls.return_value = mock_comparator
            mock_strategy = Mock()
            mock_create_strategy.return_value = mock_strategy

            # Mock one potential pair to trigger summary printing
            archive_path = Mock(spec=Path)
            archive_path.name = "test.zip"
            directory_path = Mock(spec=Path)
            directory_path.name = "test"

            from unclutter_directory.comparison import ComparisonResult

            mock_result = ComparisonResult(
                archive_path=archive_path,
                directory_path=directory_path,
                identical=False,
                archive_files=[],
                directory_files=[],
                differences=["diff1"],
            )

            mock_comparator.find_potential_duplicates = Mock(
                return_value=[(archive_path, directory_path)]
            )
            mock_comparator.compare_archive_and_directory.return_value = mock_result
            mock_comparator.get_comparison_summary = Mock(
                return_value={
                    "identical": 0,
                    "identical_percentage": 0.0,
                    "different": 1,
                }
            )

            command = DeleteUnpackedCommand(self.mock_config)
            command.execute()

            # Verify summary was printed
            mock_comparator.get_comparison_summary.assert_called_once()

    def test_print_summary(self):
        """Test _print_summary method"""
        from unclutter_directory.comparison import ComparisonResult

        # Create command instance
        with patch(
            "unclutter_directory.commands.delete_unpacked_command.ArchiveDirectoryComparator"
        ), patch(
            "unclutter_directory.commands.delete_unpacked_command.create_delete_strategy"
        ):
            command = DeleteUnpackedCommand(self.mock_config)

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

        with patch(
            "unclutter_directory.commands.delete_unpacked_command.logger"
        ) as mock_logger:
            command._print_summary(results, 1, 2)

        # Verify summary logging calls
        mock_logger.info.assert_any_call("\n📊 Summary:")
        mock_logger.info.assert_any_call("   • Total pairs checked: 2")
        mock_logger.info.assert_any_call("   • Identical structures: 1 (50.0%)")

    # Integration tests using real files and directories
    def test_execute_no_duplicates_integration(self):
        """Test execute with archive and non-matching directory - integration test"""
        # Create archive
        archive_path = self.test_path / "test.zip"
        with open(archive_path, "wb") as f:
            # Create a simple ZIP file
            with zipfile.ZipFile(f, "w") as zf:
                zf.writestr("file1.txt", "content1")
                zf.writestr("file2.txt", "content2")

        # Create non-matching directory
        dir_path = self.test_path / "different_structure"
        dir_path.mkdir()
        (dir_path / "file_a.txt").write_text("different_content_a")
        (dir_path / "file_b.txt").write_text("different_content_b")
        (dir_path / "extra_file.txt").write_text("extra")  # Additional file

        # Create config
        config = DeleteUnpackedConfig(
            target_dir=self.test_path,
            dry_run=True,  # Safe mode
            always_delete=False,
            never_delete=False,
            include_hidden=False,
            quiet=True,
        )

        command = DeleteUnpackedCommand(config)
        command.execute()

        # Verify directory still exists (no deletion occurred)
        self.assertTrue(dir_path.exists())

        # Clean up
        archive_path.unlink()
        import shutil

        shutil.rmtree(dir_path)

    def test_execute_identical_pair_dry_run_integration(self):
        """Test execute with identical archive and directory pair using --dry-run"""
        # Create content for our test files
        content1 = "This is file 1 content"
        content2 = "This is file 2 content"

        # Use unique names for this test
        test_name = "dry_run"
        content_dir_name = f"source_{test_name}"
        dir_name = f"source_{test_name}"

        # Create temporary directory for test content
        test_content_dir = self.test_path / content_dir_name
        test_content_dir.mkdir(exist_ok=True)

        # Create files in the source directory
        file1_path = test_content_dir / "file1.txt"
        file2_path = test_content_dir / "file2.txt"
        file1_path.write_text(content1)
        file2_path.write_text(content2)

        # Create ZIP archive from the source directory
        archive_path = self.test_path / f"{dir_name}.zip"
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.write(file1_path, file1_path.name)
            zf.write(file2_path, file2_path.name)

        # Create the unpacked directory (named after archive without extension)
        unpacked_dir = self.test_path / dir_name
        if not unpacked_dir.exists():
            unpacked_dir.mkdir()
        (unpacked_dir / "file1.txt").write_text(content1)
        (unpacked_dir / "file2.txt").write_text(content2)

        # Create config with dry run mode
        config = DeleteUnpackedConfig(
            target_dir=self.test_path,
            never_delete=True,  # Dry run mode - should NOT delete anything
            always_delete=False,
            include_hidden=False,
            quiet=True,
        )

        command = DeleteUnpackedCommand(config)
        command.execute()

        # Verify directory still exists (dry run should not delete)
        self.assertTrue(unpacked_dir.exists())

        # Clean up
        archive_path.unlink()
        shutil.rmtree(test_content_dir)
        if unpacked_dir.exists():
            shutil.rmtree(unpacked_dir)

    def test_execute_identical_pair_always_delete_integration(self):
        """Test execute with identical archive and directory pair using --always-delete"""
        import uuid

        # Create content for our test files
        content1 = "This is file 1 content"
        content2 = "This is file 2 content"

        # Use UUID to ensure complete uniqueness
        unique_id = str(uuid.uuid4())[:8]
        content_dir_name = f"source_always_{unique_id}"
        dir_name = f"source_always_{unique_id}"

        # Create temporary directory for test content
        test_content_dir = self.test_path / content_dir_name
        if test_content_dir.exists():
            shutil.rmtree(test_content_dir)
        test_content_dir.mkdir(parents=True)

        # Create files in the source directory
        file1_path = test_content_dir / "file1.txt"
        file2_path = test_content_dir / "file2.txt"
        file1_path.write_text(content1)
        file2_path.write_text(content2)

        # Create ZIP archive from the source directory
        archive_path = self.test_path / f"{dir_name}.zip"
        if archive_path.exists():
            archive_path.unlink()
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.write(file1_path, file1_path.name)
            zf.write(file2_path, file2_path.name)

        # Create the unpacked directory (named after archive without extension)
        unpacked_dir = self.test_path / dir_name
        if unpacked_dir.exists():
            shutil.rmtree(unpacked_dir)
        unpacked_dir.mkdir(parents=True)
        (unpacked_dir / "file1.txt").write_text(content1)
        (unpacked_dir / "file2.txt").write_text(content2)

        # Create config with always-delete mode
        config = DeleteUnpackedConfig(
            target_dir=self.test_path,
            dry_run=False,
            always_delete=True,  # Should delete automatically
            never_delete=False,
            include_hidden=False,
            quiet=True,
        )

        command = DeleteUnpackedCommand(config)
        command.execute()

        # Verify directory was actually deleted
        self.assertFalse(unpacked_dir.exists())

        # Clean up archive and content directory
        if archive_path.exists():
            archive_path.unlink()
        if test_content_dir.exists():
            shutil.rmtree(test_content_dir)

    @patch("builtins.input")
    def test_execute_identical_pair_interactive_yes_integration(self, mock_input):
        """Test execute with identical pair in interactive mode, user confirms yes"""
        mock_input.return_value = "y"

        # Create content for our test files
        content1 = "This is file 1 content"
        content2 = "This is file 2 content"

        # Use unique names for this test
        test_name = "interactive_yes"
        content_dir_name = f"source_{test_name}"
        dir_name = f"source_{test_name}"

        # Create temporary directory for test content
        test_content_dir = self.test_path / content_dir_name
        test_content_dir.mkdir(exist_ok=True)

        # Create files in the source directory
        file1_path = test_content_dir / "file1.txt"
        file2_path = test_content_dir / "file2.txt"
        file1_path.write_text(content1)
        file2_path.write_text(content2)

        # Create ZIP archive from the source directory
        archive_path = self.test_path / f"{dir_name}.zip"
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.write(file1_path, file1_path.name)
            zf.write(file2_path, file2_path.name)

        # Create the unpacked directory
        unpacked_dir = self.test_path / dir_name
        unpacked_dir.mkdir(exist_ok=True)
        (unpacked_dir / "file1.txt").write_text(content1)
        (unpacked_dir / "file2.txt").write_text(content2)

        # Create config with interactive mode
        config = DeleteUnpackedConfig(
            target_dir=self.test_path,
            dry_run=False,
            always_delete=False,  # Interactive mode
            never_delete=False,
            include_hidden=False,
            quiet=True,
        )

        command = DeleteUnpackedCommand(config)
        command.execute()

        # Verify directory was deleted after user confirmation
        self.assertFalse(unpacked_dir.exists())

        # Clean up archive
        archive_path.unlink()
        if test_content_dir.exists():
            shutil.rmtree(test_content_dir)

    @patch("builtins.input")
    def test_execute_identical_pair_interactive_no_integration(self, mock_input):
        """Test execute with identical pair in interactive mode, user confirms no"""
        mock_input.return_value = "n"

        # Create content for our test files
        content1 = "This is file 1 content"
        content2 = "This is file 2 content"

        # Use unique names for this test
        test_name = "interactive_no"
        content_dir_name = f"source_{test_name}"
        dir_name = f"source_{test_name}"

        # Create temporary directory for test content
        test_content_dir = self.test_path / content_dir_name
        test_content_dir.mkdir(exist_ok=True)

        # Create files in the source directory
        file1_path = test_content_dir / "file1.txt"
        file2_path = test_content_dir / "file2.txt"
        file1_path.write_text(content1)
        file2_path.write_text(content2)

        # Create ZIP archive from the source directory
        archive_path = self.test_path / f"{dir_name}.zip"
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.write(file1_path, file1_path.name)
            zf.write(file2_path, file2_path.name)

        # Create the unpacked directory
        unpacked_dir = self.test_path / dir_name
        unpacked_dir.mkdir(exist_ok=True)
        (unpacked_dir / "file1.txt").write_text(content1)
        (unpacked_dir / "file2.txt").write_text(content2)

        # Create config with interactive mode
        config = DeleteUnpackedConfig(
            target_dir=self.test_path,
            dry_run=False,
            always_delete=False,  # Interactive mode
            never_delete=False,
            include_hidden=False,
            quiet=True,
        )

        command = DeleteUnpackedCommand(config)
        command.execute()

        # Verify directory still exists (not deleted after user said no)
        self.assertTrue(unpacked_dir.exists())

        # Clean up
        archive_path.unlink()
        shutil.rmtree(test_content_dir)
        if unpacked_dir.exists():
            shutil.rmtree(unpacked_dir)

    def test_execute_different_structures_integration(self):
        """Test execute with archive and directory having different contents"""
        # Create archive with certain content
        archive_path = self.test_path / "test.zip"
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("file1.txt", "archive_content_1")
            zf.writestr("file2.txt", "archive_content_2")
            zf.writestr("only_in_archive.txt", "archive_only")

        # Create different directory
        unpacked_dir = self.test_path / "test"
        unpacked_dir.mkdir()
        (unpacked_dir / "file1.txt").write_text("dir_content_1")  # Different content
        (unpacked_dir / "file2.txt").write_text("archive_content_2")  # Same
        (unpacked_dir / "only_in_dir.txt").write_text("dir_only")  # Extra file

        # Create config
        config = DeleteUnpackedConfig(
            target_dir=self.test_path,
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
        self.assertTrue(unpacked_dir.exists())

        # Verify difference messages were logged
        difference_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "different" in str(call).lower() or "diff" in str(call).lower()
        ]
        self.assertTrue(len(difference_calls) > 0)

        # Clean up
        archive_path.unlink()
        shutil.rmtree(unpacked_dir)

    def test_execute_include_hidden_flag_integration(self):
        """Test --include-hidden flag affects comparison results"""
        # Create archive without hidden files
        archive_path = self.test_path / "test_hidden.zip"
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("file2.txt", "content2")

        # Create directory with a hidden file (difference)
        unpacked_dir = self.test_path / "test_hidden"
        unpacked_dir.mkdir()
        (unpacked_dir / "file1.txt").write_text("content1")
        (unpacked_dir / "file2.txt").write_text("content2")
        (unpacked_dir / ".hidden_file").write_text("hidden_content")

        # Test WITHOUT --include-hidden (hidden files ignored)
        config_without_hidden = DeleteUnpackedConfig(
            target_dir=self.test_path,
            dry_run=True,
            always_delete=False,
            never_delete=False,
            include_hidden=False,  # Should ignore hidden files
            quiet=True,
        )

        command_without = DeleteUnpackedCommand(config_without_hidden)
        with patch(
            "unclutter_directory.commands.delete_unpacked_command.logger"
        ) as mock_logger:
            command_without.execute()

        # Should report as identical (ignoring hidden file)

        # Clean up for next test
        if unpacked_dir.exists():
            shutil.rmtree(unpacked_dir)
        unpacked_dir.mkdir()
        (unpacked_dir / "file1.txt").write_text("content1")
        (unpacked_dir / "file2.txt").write_text("content2")
        (unpacked_dir / ".hidden_file").write_text("hidden_content")

        # Test WITH --include-hidden (hidden files included)
        config_with_hidden = DeleteUnpackedConfig(
            target_dir=self.test_path,
            dry_run=True,
            always_delete=False,
            never_delete=False,
            include_hidden=True,  # Should include hidden files
            quiet=True,
        )

        command_with = DeleteUnpackedCommand(config_with_hidden)
        with patch(
            "unclutter_directory.commands.delete_unpacked_command.logger"
        ) as mock_logger:
            command_with.execute()

        # Should report differences due to hidden file
        difference_calls = [
            call
            for call in mock_logger.info.call_args_list
            if "different" in str(call).lower() or "diff" in str(call).lower()
        ]
        self.assertTrue(len(difference_calls) > 0)

        # Clean up
        archive_path.unlink()
        shutil.rmtree(unpacked_dir)


class TestDeleteUnpackedCommandConfig(unittest.TestCase):
    """Tests for DeleteUnpackedConfig"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def test_config_with_quiet_flag(self):
        """Test that DeleteUnpackedConfig handles quiet flag correctly"""
        config = DeleteUnpackedConfig(target_dir=self.test_path, quiet=True)

        self.assertTrue(config.quiet)

        # Verify __str__ includes quiet flag
        str_repr = str(config)
        self.assertIn("quiet", str_repr)


if __name__ == "__main__":
    unittest.main(failfast=True)
