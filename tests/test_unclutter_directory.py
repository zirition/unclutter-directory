import shutil
import tempfile
import unittest
import click.testing
from pathlib import Path
from unittest.mock import patch, mock_open
from unclutter_directory.File import File
from unclutter_directory.unclutter_directory import _load_rules, cli


class TestUnclutterDirectory(unittest.TestCase):
    def setUp(self):
        self.mock_rules = [
            {
                "name": "Test Rule",
                "conditions": {"end": ".txt"},
                "action": {"type": "move", "target": "test_dir"},
            }
        ]

        self.mock_rules_delete = [
            {
                "name": "Test Rule Delete",
                "conditions": {"end": ".txt"},
                "action": {"type": "delete"},
            }
        ]

        # Click check that the directory and file exists, so we need to create them
        self.temp_dir = tempfile.mkdtemp()
        self.rules_path = Path(self.temp_dir) / "rules.yaml"
        self.rules_path.touch()


    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_load_rules_empty_file(self):
        with patch("builtins.open", mock_open(read_data="")):
            rules = _load_rules("dummy.yaml")
            self.assertIsNone(rules)

    def test_load_rules_file_not_found(self):
        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = FileNotFoundError()
            with self.assertRaises(FileNotFoundError):
                _load_rules("nonexistent.yaml")

    @patch("unclutter_directory.unclutter_directory.FileMatcher")
    @patch("unclutter_directory.unclutter_directory.ActionExecutor")
    @patch("unclutter_directory.unclutter_directory._load_rules")
    @patch("unclutter_directory.unclutter_directory.is_valid_rules_file")
    def test_organize_dry_run(
        self, mock_valid_rules, mock_load_rules, mock_executor, mock_matcher
    ):
        # Setup
        mock_load_rules.return_value = self.mock_rules
        mock_valid_rules.return_value = []
        mock_matcher.return_value.match.return_value = self.mock_rules[0]

        # Run organize with dry-run
        runner = click.testing.CliRunner()
        result = runner.invoke(
            cli, ["organize", str(self.temp_dir), str(self.rules_path), "--dry-run"]
        )

        self.assertEqual(result.exit_code, 0)
        mock_executor.return_value.execute_action.assert_not_called()

    @patch("unclutter_directory.unclutter_directory._load_rules")
    @patch("unclutter_directory.unclutter_directory.is_valid_rules_file")
    def test_organize_invalid_rules(self, mock_valid_rules, mock_load_rules):
        # Setup
        mock_load_rules.return_value = self.mock_rules
        mock_valid_rules.return_value = ["Error"]

        with self.assertLogs('download_organizer', level='INFO') as logger:
            # Run organize with invalid rules
            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["organize", str(self.temp_dir), str(self.rules_path)])

            self.assertEqual(result.exit_code, 0)
            self.assertIn("Invalid rules file", logger.output[0])

    def test_validate_nonexistent_file(self):
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["validate", "nonexistent.yaml"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("File 'nonexistent.yaml' does not exist", result.output)

    @patch("unclutter_directory.unclutter_directory._load_rules")
    def test_validate_empty_rules(self, mock_load_rules):
        mock_load_rules.return_value = {"rules": []}

        with self.assertLogs('download_organizer', level='INFO') as logger:
            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["validate", str(self.rules_path)])

            self.assertEqual(result.exit_code, 0)
            self.assertIn("Validation complete.", logger.output[0])


    @patch("unclutter_directory.unclutter_directory.File")
    @patch("unclutter_directory.unclutter_directory._load_rules")
    @patch("unclutter_directory.unclutter_directory.FileMatcher")
    @patch.object(Path, 'is_file')
    @patch.object(Path, 'iterdir')
    def test_organize_multiple_files(self, mock_iterdir, mock_is_file, mock_matcher, mock_load_rules, mock_file):
        mock_load_rules.return_value = self.mock_rules
        mock_matcher.return_value.match.side_effect = [
            {"action": {"type": "move", "target": "dir1"}},
            {"action": {"type": "move", "target": "dir2"}},
            None,  # No match for third file
        ]
        tmp_path = Path("/tmp/test")
        files = [tmp_path / "file1.txt", tmp_path / "file2.txt", tmp_path / "file3.txt"]

        mock_iterdir.return_value = files
        mock_is_file.return_value = True
        mock_file.from_path.return_value = File(tmp_path, files[0], 100, 100)

        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["organize", str(self.temp_dir), str(self.rules_path), '--dry-run'])

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_matcher.return_value.match.call_count, 3)

    def test_both_flags_provided(self):
      with self.assertLogs('download_organizer', level='INFO') as logger:
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ['organize', str(self.temp_dir), str(self.rules_path), '--never-delete', '--always-delete'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Options --always-delete and --never-delete are mutually exclusive.", logger.output[0])

    @patch.object(Path, 'unlink')
    @patch.object(Path, 'is_file')
    @patch.object(Path, 'iterdir')
    @patch("unclutter_directory.unclutter_directory.File")
    @patch("unclutter_directory.unclutter_directory._load_rules")
    @patch("unclutter_directory.unclutter_directory.FileMatcher")
    def test_always_delete(self, mock_matcher, mock_load_rules, mock_file, mock_iterdir, mock_is_file, mock_unlink):
        mock_load_rules.return_value = self.mock_rules_delete
        mock_matcher.return_value.match.side_effect = [
            {"action": {"type": "delete"}},
        ]
        mock_iterdir.return_value = [Path(self.temp_dir) / "test_file.txt"]
        mock_is_file.return_value = True
        mock_file.from_path.return_value = File(self.temp_dir, "test_file.txt", 100, 100)

        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["organize", str(self.temp_dir), str(self.rules_path), '--always-delete'])

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_unlink.call_count, 1)

    @patch.object(Path, 'unlink')
    @patch("unclutter_directory.unclutter_directory.File")
    @patch("unclutter_directory.unclutter_directory._load_rules")
    @patch("unclutter_directory.unclutter_directory.FileMatcher")
    def test_never_delete_rulesfile(self, mock_matcher, mock_load_rules, mock_file, mock_unlink):
        mock_load_rules.return_value = self.mock_rules_delete
        mock_matcher.return_value.match.side_effect = [
            {"action": {"type": "delete"}},
        ]
        mock_file.from_path.return_value = File(self.temp_dir, "test_file.txt", 100, 100)

        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["organize", str(self.temp_dir), str(self.rules_path), '--always-delete'])

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_unlink.call_count, 0)


    @patch.object(Path, 'unlink')
    @patch("unclutter_directory.unclutter_directory.File")
    @patch("unclutter_directory.unclutter_directory._load_rules")
    @patch("unclutter_directory.unclutter_directory.FileMatcher")
    def test_never_delete(self, mock_matcher, mock_load_rules, mock_file, mock_unlink):
        mock_load_rules.return_value = self.mock_rules_delete
        mock_matcher.return_value.match.side_effect = [
            {"action": {"type": "delete"}},
        ]
        mock_file.from_path.return_value = File(self.temp_dir, "test_file.txt", 100, 100)

        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["organize", str(self.temp_dir), str(self.rules_path), '--never-delete'])

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(mock_unlink.call_count, 0)

    @patch("unclutter_directory.unclutter_directory.FileMatcher")
    @patch("unclutter_directory.unclutter_directory._load_rules")
    @patch.object(Path, 'is_file')
    @patch.object(Path, 'iterdir')
    def test_organize_include_hidden(self, mock_iterdir, mock_is_file, mock_load_rules, mock_matcher):
        # Setup
        mock_load_rules.return_value = self.mock_rules
        mock_matcher.return_value.match.return_value = self.mock_rules[0]

        # Create a hidden file
        hidden_file_path = Path(self.temp_dir) / ".hidden_file.txt"
        hidden_file_path.touch()

        mock_iterdir.return_value = [hidden_file_path]
        mock_is_file.return_value = True

        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["organize", str(self.temp_dir), str(self.rules_path), "--include-hidden"])

        self.assertEqual(result.exit_code, 0)
        # Check that the match was called for the hidden file
        self.assertEqual(mock_matcher.return_value.match.call_count, 1)

    @patch("unclutter_directory.unclutter_directory.FileMatcher")
    @patch("unclutter_directory.unclutter_directory._load_rules")
    @patch.object(Path, 'is_file')
    @patch.object(Path, 'iterdir')
    def test_organize_not_including_hidden(self, mock_iterdir, mock_is_file, mock_load_rules, mock_matcher):
        # Setup
        mock_load_rules.return_value = self.mock_rules
        mock_matcher.return_value.match.return_value = self.mock_rules[0]

        # Create a hidden file
        hidden_file_path = Path(self.temp_dir) / ".hidden_file.txt"
        hidden_file_path.touch()

        mock_iterdir.return_value = [hidden_file_path]
        mock_is_file.return_value = True

        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["organize", str(self.temp_dir), str(self.rules_path)])

        self.assertEqual(result.exit_code, 0)
        # Check that the match was not called for the hidden file
        self.assertEqual(mock_matcher.return_value.match.call_count, 0)

    @patch("unclutter_directory.unclutter_directory.FileMatcher")
    @patch("unclutter_directory.unclutter_directory._load_rules")
    @patch.object(Path, 'is_file')
    @patch.object(Path, 'iterdir')
    def test_organize_ignore_rules_file(self, mock_iterdir, mock_is_file, mock_load_rules, mock_matcher):
        # Setup
        mock_load_rules.return_value = self.mock_rules
        mock_matcher.return_value.match.return_value = self.mock_rules[0]

        # Create a file in the directory
        regular_file_path = Path(self.temp_dir) / "file.txt"
        regular_file_path.touch()

        mock_iterdir.return_value = [self.rules_path, regular_file_path]
        mock_is_file.return_value = True

        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["organize", str(self.temp_dir), str(self.rules_path)])

        self.assertEqual(result.exit_code, 0)
        # Check that the match was not called for the rules file
        self.assertEqual(mock_matcher.return_value.match.call_count, 1)  # Only for "file.txt"


    def test_validate_alias_check(self):
        # Simulate the `validate` command execution via its alias `check`
        runner = click.testing.CliRunner()

        with self.assertLogs('download_organizer', level='INFO') as logger:
            result = runner.invoke(cli, ["check", str(self.rules_path)])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Validation complete.", logger.output[0])


    def test_abbreviations_for_commands(self):
        # Test abbreviation for `validate` command
        runner = click.testing.CliRunner()

        with self.assertLogs('download_organizer', level='INFO') as logger:
            result = runner.invoke(cli, ["val", str(self.rules_path)])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Validation complete.", logger.output[0])

        with self.assertLogs('download_organizer', level='INFO') as logger:
            # Test abbreviation for `organize` command
            result = runner.invoke(cli, ["org", str(self.temp_dir), str(self.rules_path)])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Invalid rules file", logger.output[0])

    def test_organize_execution_with_valid_directory(self):
        valid_directory_path = self.temp_dir  # Using temp_dir as a valid directory
        runner = click.testing.CliRunner()
        with self.assertLogs('download_organizer', level='INFO') as logger:
            result = runner.invoke(cli, [valid_directory_path, str(self.rules_path)])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Invalid rules file", logger.output[0])

if __name__ == "__main__":
    unittest.main()
