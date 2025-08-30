import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from unclutter_directory.execution.delete_strategy import (
    AutomaticDeleteStrategy,
    DeleteConfirmationStrategy,
    DryRunDeleteStrategy,
    InteractiveDeleteStrategy,
    create_delete_strategy,
)


class TestDeleteConfirmationStrategy(unittest.TestCase):
    """Test base DeleteConfirmationStrategy class"""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.archive_path = Path(self.temp_dir.name) / "test.zip"
        self.directory_path = Path(self.temp_dir.name) / "test_dir"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_abstract_methods(self):
        """Test that base class cannot be instantiated directly"""
        with self.assertRaises(TypeError):
            DeleteConfirmationStrategy()


class TestInteractiveDeleteStrategy(unittest.TestCase):
    """Test InteractiveDeleteStrategy class"""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.archive_path = Path(self.temp_dir.name) / "test.zip"
        self.directory_path = Path(self.temp_dir.name) / "test_dir"
        self.strategy = InteractiveDeleteStrategy()

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("builtins.input")
    @patch("unclutter_directory.execution.delete_strategy.logger")
    def test_should_delete_directory_yes_response(self, mock_logger, mock_input):
        """Test user responding 'y' to delete prompt"""
        mock_input.return_value = "y"

        result = self.strategy.should_delete_directory(
            self.directory_path, self.archive_path
        )

        self.assertTrue(result)
        mock_input.assert_called_once()

    @patch("builtins.input")
    @patch("unclutter_directory.execution.delete_strategy.logger")
    def test_should_delete_directory_no_response(self, mock_logger, mock_input):
        """Test user responding 'n' to delete prompt"""
        mock_input.return_value = "n"

        result = self.strategy.should_delete_directory(
            self.directory_path, self.archive_path
        )

        self.assertFalse(result)
        mock_input.assert_called_once()

    @patch("builtins.input")
    @patch("unclutter_directory.execution.delete_strategy.logger")
    def test_should_delete_directory_empty_response(self, mock_logger, mock_input):
        """Test user responding with empty string (defaults to no)"""
        mock_input.return_value = ""

        result = self.strategy.should_delete_directory(
            self.directory_path, self.archive_path
        )

        self.assertFalse(result)

    @patch("builtins.input")
    @patch("unclutter_directory.execution.delete_strategy.logger")
    def test_should_delete_directory_invalid_response_then_valid(
        self, mock_logger, mock_input
    ):
        """Test invalid response followed by valid response"""
        mock_input.side_effect = ["invalid", "y"]

        result = self.strategy.should_delete_directory(
            self.directory_path, self.archive_path
        )

        self.assertTrue(result)
        self.assertEqual(mock_input.call_count, 2)

    @patch("unclutter_directory.execution.delete_strategy.logger")
    def test_should_delete_directory_keyboard_interrupt(self, mock_logger):
        """Test handling KeyboardInterrupt during input"""
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.strategy.should_delete_directory(
                    self.directory_path, self.archive_path
                )

    def test_perform_deletion_success(self):
        """Test successful directory deletion"""
        with patch("shutil.rmtree") as mock_rmtree:
            with patch(
                "unclutter_directory.execution.delete_strategy.logger"
            ) as mock_logger:
                result = self.strategy.perform_deletion(
                    self.directory_path, self.archive_path
                )

                self.assertTrue(result)
                mock_rmtree.assert_called_once_with(self.directory_path)
                mock_logger.info.assert_called_once()

    def test_perform_deletion_error(self):
        """Test handling deletion failure"""
        with patch("shutil.rmtree", side_effect=OSError("Permission denied")):
            with patch(
                "unclutter_directory.execution.delete_strategy.logger"
            ) as mock_logger:
                result = self.strategy.perform_deletion(
                    self.directory_path, self.archive_path
                )

                self.assertFalse(result)
                mock_logger.error.assert_called_once()

    def test_perform_deletion_directory_not_exists(self):
        """Test deletion when directory doesn't exist"""
        with patch(
            "shutil.rmtree", side_effect=FileNotFoundError("No such file or directory")
        ):
            with patch(
                "unclutter_directory.execution.delete_strategy.logger"
            ) as mock_logger:
                result = self.strategy.perform_deletion(
                    self.directory_path, self.archive_path
                )

                self.assertFalse(result)
                mock_logger.error.assert_called_once()

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    @patch("pathlib.Path.rmdir")
    def test_perform_deletion_rmdir_error(self, mock_rmdir, mock_is_file, mock_exists):
        """Test handling rmdir failure"""
        mock_exists.return_value = True
        mock_is_file.return_value = False
        mock_rmdir.side_effect = OSError("Permission denied")

        with patch(
            "unclutter_directory.execution.delete_strategy.logger"
        ) as mock_logger:
            result = self.strategy.perform_deletion(
                self.directory_path, self.archive_path
            )

            self.assertFalse(result)
            mock_logger.error.assert_called_once()


class TestAutomaticDeleteStrategy(unittest.TestCase):
    """Test AutomaticDeleteStrategy class"""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.archive_path = Path(self.temp_dir.name) / "test.zip"
        self.directory_path = Path(self.temp_dir.name) / "test_dir"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_init_defaults(self):
        """Test initialization with default values"""
        strategy = AutomaticDeleteStrategy()
        self.assertFalse(strategy.always_delete)
        self.assertFalse(strategy.never_delete)

    def test_init_with_flags(self):
        """Test initialization with specific flags"""
        strategy = AutomaticDeleteStrategy(always_delete=True, never_delete=False)
        self.assertTrue(strategy.always_delete)
        self.assertFalse(strategy.never_delete)

    def test_should_delete_directory_always_delete_true(self):
        """Test should_delete when always_delete is True"""
        strategy = AutomaticDeleteStrategy(always_delete=True)
        result = strategy.should_delete_directory(
            self.directory_path, self.archive_path
        )
        self.assertTrue(result)

    def test_should_delete_directory_never_delete_true(self):
        """Test should_delete when never_delete is True"""
        strategy = AutomaticDeleteStrategy(never_delete=True)
        result = strategy.should_delete_directory(
            self.directory_path, self.archive_path
        )
        self.assertFalse(result)

    def test_should_delete_directory_both_false(self):
        """Test should_delete when both flags are False"""
        strategy = AutomaticDeleteStrategy()
        result = strategy.should_delete_directory(
            self.directory_path, self.archive_path
        )
        self.assertFalse(result)

    def test_should_delete_directory_both_true(self):
        """Test should_delete when both flags are True (never_delete takes precedence)"""
        strategy = AutomaticDeleteStrategy(always_delete=True, never_delete=True)
        result = strategy.should_delete_directory(
            self.directory_path, self.archive_path
        )
        self.assertFalse(result)

    @patch("unclutter_directory.execution.delete_strategy.logger")
    def test_should_delete_directory_never_delete_logging(self, mock_logger):
        """Test logging when never_delete flag is used"""
        strategy = AutomaticDeleteStrategy(never_delete=True)

        result = strategy.should_delete_directory(
            self.directory_path, self.archive_path
        )

        self.assertFalse(result)
        mock_logger.info.assert_called_once_with(
            f"Skipping deletion of {self.directory_path} (never-delete mode)"
        )

    def test_should_delete_directory_both_false_logging(self):
        """Test behavior when both flags are False"""
        strategy = AutomaticDeleteStrategy()

        result = strategy.should_delete_directory(
            self.directory_path, self.archive_path
        )

        # Both flags false defaults to never delete (no specific warning logged)
        self.assertFalse(result)


class TestDryRunDeleteStrategy(unittest.TestCase):
    """Test DryRunDeleteStrategy class"""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.archive_path = Path(self.temp_dir.name) / "test.zip"
        self.directory_path = Path(self.temp_dir.name) / "test_dir"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_should_delete_directory_implementation(self):
        """Test that should_delete_directory always returns False in dry run mode"""
        strategy = DryRunDeleteStrategy()
        result = strategy.should_delete_directory(
            self.directory_path, self.archive_path
        )
        self.assertFalse(result)  # Dry run always returns False

    @patch("unclutter_directory.execution.delete_strategy.logger")
    def test_perform_deletion_dry_run_true(self, mock_logger):
        """Test deletion in dry run mode"""
        strategy = DryRunDeleteStrategy()
        result = strategy.perform_deletion(
            self.directory_path, self.archive_path, dry_run=True
        )

        self.assertTrue(result)  # Always returns True in dry run
        mock_logger.info.assert_called_once()

    @patch("unclutter_directory.execution.delete_strategy.logger")
    def test_perform_deletion_dry_run_false(self, mock_logger):
        """Test deletion in normal mode (dry_run=False)"""
        strategy = DryRunDeleteStrategy()
        result = strategy.perform_deletion(
            self.directory_path, self.archive_path, dry_run=False
        )

        self.assertTrue(result)  # Returns True even without actual deletion logic
        mock_logger.info.assert_called_once()


class TestCreateDeleteStrategy(unittest.TestCase):
    """Test create_delete_strategy factory function"""

    def test_create_interactive_strategy_default(self):
        """Test creating InteractiveDeleteStrategy by default"""
        strategy = create_delete_strategy()
        self.assertIsInstance(strategy, InteractiveDeleteStrategy)

    def test_create_interactive_strategy_explicit(self):
        """Test creating InteractiveDeleteStrategy explicitly"""
        strategy = create_delete_strategy(
            dry_run=False, always_delete=False, never_delete=False
        )
        self.assertIsInstance(strategy, InteractiveDeleteStrategy)

    def test_create_dry_run_strategy(self):
        """Test creating DryRunDeleteStrategy"""
        strategy = create_delete_strategy(
            dry_run=True, always_delete=False, never_delete=False
        )
        self.assertIsInstance(strategy, DryRunDeleteStrategy)

    def test_create_automatic_strategy_always_delete(self):
        """Test creating AutomaticDeleteStrategy with always_delete"""
        strategy = create_delete_strategy(
            dry_run=False, always_delete=True, never_delete=False
        )
        self.assertIsInstance(strategy, AutomaticDeleteStrategy)
        self.assertTrue(strategy.always_delete)
        self.assertFalse(strategy.never_delete)

    def test_create_automatic_strategy_never_delete(self):
        """Test creating AutomaticDeleteStrategy with never_delete"""
        strategy = create_delete_strategy(
            dry_run=False, always_delete=False, never_delete=True
        )
        self.assertIsInstance(strategy, AutomaticDeleteStrategy)
        self.assertFalse(strategy.always_delete)
        self.assertTrue(strategy.never_delete)

    def test_create_automatic_strategy_both_flags(self):
        """Test creating AutomaticDeleteStrategy with both flags"""
        strategy = create_delete_strategy(
            dry_run=False, always_delete=True, never_delete=True
        )
        self.assertIsInstance(strategy, AutomaticDeleteStrategy)
        self.assertTrue(strategy.always_delete)
        self.assertTrue(strategy.never_delete)


if __name__ == "__main__":
    unittest.main(failfast=True)
