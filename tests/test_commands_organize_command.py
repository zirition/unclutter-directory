import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

from unclutter_directory.commands.organize_command import OrganizeCommand
from unclutter_directory.config.organize_config import OrganizeConfig
from unclutter_directory.factories.component_factory import ComponentFactory
from unclutter_directory.validation.validation_chain import ValidationChain


class TestOrganizeCommand(unittest.TestCase):
    """
    Comprehensive unit tests for OrganizeCommand class
    """

    def setUp(self):
        """Set up test environment with temporary directory"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.temp_dir.name)

        # Create mock config
        self.mock_config = Mock(spec=OrganizeConfig)
        self.mock_config.target_dir = self.test_path
        self.mock_config.rules_file_path = self.test_path / "rules.yaml"
        self.mock_config.dry_run = False
        self.mock_config.quiet = False

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def test_init(self):
        """Test OrganizeCommand initialization"""
        command = OrganizeCommand(self.mock_config)

        # Verify attributes are set correctly
        self.assertEqual(command.config, self.mock_config)
        self.assertIsInstance(command.validation_chain, ValidationChain)
        self.assertIsInstance(command.factory, ComponentFactory)
        self.assertEqual(command.rule_responses, {})

    @patch("unclutter_directory.commands.organize_command.setup_logging")
    def test_setup_logging_quiet_mode(self, mock_setup_logging):
        """Test logging setup in quiet mode"""
        self.mock_config.quiet = True

        command = OrganizeCommand(self.mock_config)
        command._setup_logging()

        # Verify setup_logging is called with True
        mock_setup_logging.assert_called_once_with(True)

    @patch("unclutter_directory.commands.organize_command.setup_logging")
    def test_setup_logging_verbose_mode(self, mock_setup_logging):
        """Test logging setup in verbose mode"""
        self.mock_config.quiet = False

        command = OrganizeCommand(self.mock_config)
        command._setup_logging()

        # Verify setup_logging is called with False
        mock_setup_logging.assert_called_once_with(False)


class TestOrganizeCommandValidation(unittest.TestCase):
    """Tests for configuration validation functionality"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.temp_dir.name)

        self.mock_config = Mock(spec=OrganizeConfig)
        self.mock_config.target_dir = self.test_path

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    @patch("unclutter_directory.commands.organize_command.ValidationChain")
    @patch("unclutter_directory.commands.organize_command.sys.exit")
    def test_validate_config_no_errors(self, mock_exit, mock_validation_chain_cls):
        """Test validation with no errors"""
        # Setup mock validation chain
        mock_validation_chain = Mock()
        mock_validation_chain.validate.return_value = []
        mock_validation_chain_cls.return_value = mock_validation_chain

        command = OrganizeCommand(self.mock_config)
        command._validate_config()

        # Verify validate was called and exit was not called
        mock_validation_chain.validate.assert_called_once_with(self.mock_config)
        mock_exit.assert_not_called()

    @patch("unclutter_directory.commands.organize_command.logger")
    @patch("unclutter_directory.commands.organize_command.ValidationChain")
    @patch("unclutter_directory.commands.organize_command.sys.exit")
    def test_validate_config_with_errors(
        self, mock_exit, mock_validation_chain_cls, mock_logger
    ):
        """Test validation with errors"""
        # Setup mock validation chain with errors
        mock_validation_chain = Mock()
        mock_validation_chain.validate.return_value = ["Error 1", "Error 2"]
        mock_validation_chain_cls.return_value = mock_validation_chain

        command = OrganizeCommand(self.mock_config)
        command._validate_config()

        # Verify validate was called
        mock_validation_chain.validate.assert_called_once_with(self.mock_config)

        # Verify error logging with correct calls
        expected_calls = [
            call("Configuration validation failed:"),
            call("  • Error 1"),
            call("  • Error 2"),
        ]
        self.assertEqual(mock_logger.error.call_args_list, expected_calls)

        # Verify exit was called with code 1
        mock_exit.assert_called_once_with(1)


class TestOrganizeCommandProcessing(unittest.TestCase):
    """Tests for file processing functionality"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.temp_dir.name)

        self.mock_config = Mock(spec=OrganizeConfig)
        self.mock_config.target_dir = self.test_path
        self.mock_config.rules_file_path = self.test_path / "rules.yaml"
        self.mock_config.dry_run = False

        # Create mock components
        self.mock_matcher = Mock()
        self.mock_collector = Mock()
        self.mock_strategy = Mock()
        self.mock_processor = Mock()

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    @patch("unclutter_directory.commands.organize_command.logger")
    @patch("unclutter_directory.commands.organize_command.FileProcessor")
    @patch("unclutter_directory.commands.organize_command.ComponentFactory")
    def test_process_files_no_files_found(
        self, mock_factory_cls, mock_processor_cls, mock_logger
    ):
        """Test processing when no files are found"""
        # Setup factory mocks
        mock_factory = Mock()
        mock_factory.create_file_matcher.return_value = self.mock_matcher
        mock_factory.create_file_collector.return_value = self.mock_collector
        mock_factory.create_execution_strategy.return_value = self.mock_strategy
        mock_factory_cls.return_value = mock_factory

        # Setup collector to return empty list
        self.mock_collector.collect.return_value = []

        # Setup processor
        mock_processor = Mock()
        mock_processor_cls.return_value = mock_processor

        command = OrganizeCommand(self.mock_config)
        command._process_files()

        # Verify collector was called
        self.mock_collector.collect.assert_called_once_with(self.mock_config.target_dir)

        # Verify no processing occurred
        mock_processor_cls.assert_not_called()
        mock_logger.info.assert_called_once_with("No files found to process")

    @patch("unclutter_directory.commands.organize_command.logger")
    @patch("unclutter_directory.commands.organize_command.FileProcessor")
    @patch("unclutter_directory.commands.organize_command.ComponentFactory")
    def test_process_files_successful_processing(
        self, mock_factory_cls, mock_processor_cls, mock_logger
    ):
        """Test successful file processing"""
        # Setup factory mocks
        mock_factory = Mock()
        mock_factory.create_file_matcher.return_value = self.mock_matcher
        mock_factory.create_file_collector.return_value = self.mock_collector
        mock_factory.create_execution_strategy.return_value = self.mock_strategy
        mock_factory_cls.return_value = mock_factory

        # Setup collector to return files
        test_files = [self.test_path / "file1.txt", self.test_path / "file2.txt"]
        self.mock_collector.collect.return_value = test_files

        # Setup processor with stats
        test_stats = {
            "total_files": 2,
            "processed_files": 2,
            "skipped_files": 0,
            "errors": 0,
        }
        mock_processor = Mock()
        mock_processor.process_files.return_value = test_stats
        mock_processor_cls.return_value = mock_processor

        command = OrganizeCommand(self.mock_config)
        command._process_files()

        # Verify all components were created
        mock_factory.create_file_matcher.assert_called_once_with(self.mock_config)
        mock_factory.create_file_collector.assert_called_once_with(self.mock_config)
        mock_factory.create_execution_strategy.assert_called_once_with(self.mock_config)

        # Verify processor was created and called
        mock_processor_cls.assert_called_once_with(
            self.mock_matcher, self.mock_strategy, command.rule_responses
        )
        mock_processor.process_files.assert_called_once_with(
            test_files, self.mock_config.target_dir
        )

        # Verify summary logging was called
        self.assertTrue(mock_logger.info.called)


class TestOrganizeCommandLogging(unittest.TestCase):
    """Tests for processing summary logging"""

    @patch("unclutter_directory.commands.organize_command.logger")
    def test_log_processing_summary_dry_run(self, mock_logger):
        """Test logging summary in dry run mode"""
        mock_config = Mock()
        mock_config.dry_run = True

        command = OrganizeCommand(mock_config)

        # Test stats
        stats = {
            "total_files": 10,
            "processed_files": 8,
            "skipped_files": 2,
            "errors": 0,
        }

        command._log_processing_summary(stats)

        # Verify dry run message (including skipped files notification)
        expected_calls = [
            call("Dry run completed: 8/10 files would be processed"),
            call("  • 2 files skipped (no matching rules)"),
        ]
        self.assertEqual(mock_logger.info.call_args_list, expected_calls)
        mock_logger.warning.assert_not_called()

    @patch("unclutter_directory.commands.organize_command.logger")
    def test_log_processing_summary_normal_run(self, mock_logger):
        """Test logging summary in normal run mode"""
        mock_config = Mock()
        mock_config.dry_run = False

        command = OrganizeCommand(mock_config)

        # Test stats
        stats = {
            "total_files": 10,
            "processed_files": 7,
            "skipped_files": 2,
            "errors": 1,
        }

        command._log_processing_summary(stats)

        # Verify normal run messages
        expected_calls = [
            call("Processing completed: 7/10 files processed"),
            call("  • 2 files skipped (no matching rules)"),
        ]
        self.assertEqual(mock_logger.info.call_args_list, expected_calls)
        mock_logger.warning.assert_called_once_with(
            "  • 1 files had errors during processing"
        )


class TestOrganizeCommandExecution(unittest.TestCase):
    """Tests for the main execute method"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.temp_dir.name)

        self.mock_config = Mock(spec=OrganizeConfig)
        self.mock_config.target_dir = self.test_path

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    @patch.object(OrganizeCommand, "_process_files")
    @patch.object(OrganizeCommand, "_validate_config")
    @patch.object(OrganizeCommand, "_setup_logging")
    def test_execute_successful_flow(
        self, mock_setup_logging, mock_validate_config, mock_process_files
    ):
        """Test successful execution flow"""
        command = OrganizeCommand(self.mock_config)
        command.execute()

        # Verify all steps were called in correct order
        mock_setup_logging.assert_called_once()
        mock_validate_config.assert_called_once()
        mock_process_files.assert_called_once()

    @patch("unclutter_directory.commands.organize_command.logger")
    @patch.object(OrganizeCommand, "_setup_logging")
    def test_execute_keyboard_interrupt(self, mock_setup_logging, mock_logger):
        """Test execution with KeyboardInterrupt"""
        command = OrganizeCommand(self.mock_config)

        # Make _validate_config raise KeyboardInterrupt
        with patch.object(command, "_validate_config", side_effect=KeyboardInterrupt()):
            command.execute()

            # Verify interrupt was handled
            mock_logger.info.assert_called_once_with("\nOperation cancelled by user")

    @patch("unclutter_directory.commands.organize_command.logger")
    @patch.object(OrganizeCommand, "_setup_logging")
    def test_execute_generic_exception(self, mock_setup_logging, mock_logger):
        """Test execution with generic exception"""
        command = OrganizeCommand(self.mock_config)

        # Make _validate_config raise generic exception
        test_exception = ValueError("Test error")
        with patch.object(command, "_validate_config", side_effect=test_exception):
            with self.assertRaises(ValueError):
                command.execute()

            # Verify error was logged
            mock_logger.error.assert_called_once_with(
                f"Unexpected error during organize operation: {test_exception}"
            )


if __name__ == "__main__":
    unittest.main(failfast=True)
