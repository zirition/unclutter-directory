import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

import click.testing

from unclutter_directory.unclutter_directory import (
    _load_rules,
    _collect_files,
    _should_exclude_rules_file,
    _handle_deletion,
    cli,
    prompt_user_for_action,
)


class TestUnclutterDirectory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        
        self.mock_rules = [{
            "conditions": {"end": ".txt"},
            "action": {"type": "move", "target": "test_dir"},
        }, {
            "conditions": {"end": ".tmp"},
            "action": {"type": "delete"},
        }]

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_load_rules_success(self):
        with patch("builtins.open", mock_open(read_data="test: data")) as mock_file, \
             patch("yaml.safe_load", return_value=self.mock_rules) as mock_load:
            rules = _load_rules("dummy.yaml")
            
            mock_file.assert_called_with("dummy.yaml", "r")
            mock_load.assert_called_once()
            self.assertEqual(rules, self.mock_rules)

    def test_load_rules_invalid_file(self):
        with patch("builtins.open") as mock_file:
            mock_file.side_effect = FileNotFoundError("Test error")
            rules = _load_rules("missing.yaml")
            self.assertIsNone(rules)

    def test_collect_files_hidden_inclusion(self):
        # Create test files
        (self.temp_dir / "visible.txt").touch()
        (self.temp_dir / ".hidden").touch()

        files = _collect_files(self.temp_dir, include_hidden=True)
        self.assertEqual(len(files), 2)

        files = _collect_files(self.temp_dir, include_hidden=False)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "visible.txt")

    def test_should_exclude_rules_file(self):
        target_dir = self.temp_dir
        rules_file = self.temp_dir / "rules.yaml"
        rules_file.touch()

        test_file = target_dir / "data.txt"
        self.assertFalse(_should_exclude_rules_file(test_file, rules_file, target_dir))
        self.assertTrue(_should_exclude_rules_file(rules_file, rules_file, target_dir))

    @patch("unclutter_directory.unclutter_directory._process_file")
    @patch("unclutter_directory.unclutter_directory.FileMatcher")
    @patch("unclutter_directory.unclutter_directory._load_rules")
    def test_organize_happy_path(
        self, mock_load, mock_matcher, mock_process
    ):
        rules_file = self.temp_dir / ".unclutter_rules.yaml"
        rules_file.touch()

        matched_file = self.temp_dir / "matched.txt"
        matched_file.touch()

        mock_load.return_value = self.mock_rules
        mock_matcher.return_value = MagicMock()

        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["organize", str(self.temp_dir)])
        
        self.assertEqual(result.exit_code, 0)
        mock_process.assert_called()

    @patch("unclutter_directory.unclutter_directory._handle_deletion")
    @patch("unclutter_directory.unclutter_directory._load_rules")
    def test_process_file_delete_action(self, mock_load, mock_handle):
        rules_file = self.temp_dir / ".unclutter_rules.yaml"
        rules_file.touch()

        mock_load.return_value = self.mock_rules

        file_path = self.temp_dir / "test.tmp"
        file_path.touch()
        
        runner = click.testing.CliRunner()
        result = runner.invoke(
            cli, ["organize", str(self.temp_dir), "--always-delete"]
        )

        self.assertEqual(result.exit_code, 0)
        mock_handle.assert_called()

    @patch("builtins.input")
    def test_prompt_user_responses(self, mock_input):
        test_cases = [
            ("y", "y"), ("", "y"), ("A", "a"), ("never", "never")
        ]
        
        for input_val, expected in test_cases:
            with self.subTest(input=input_val):
                mock_input.return_value = input_val
                response = prompt_user_for_action(Path("test.txt"))
                self.assertEqual(response, expected)

    def test_handle_deletion_flags(self):
        mock_rule = {"action": {"type": "delete"}}
        
        # Test always delete
        result = _handle_deletion(Path("test.txt"), mock_rule, {}, True, False)
        self.assertTrue(result)

        # Test never delete
        result = _handle_deletion(Path("test.txt"), mock_rule, {}, False, True)
        self.assertFalse(result)

    @patch("unclutter_directory.unclutter_directory._load_rules")
    def test_validate_command(self, mock_load):
        rules_file = self.temp_dir / "test_rules.yaml"
        rules_file.touch()

        mock_load.return_value = self.mock_rules
        
        with self.assertLogs('unclutter_directory', level='INFO') as log:
            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["validate", str(rules_file)])
            
            self.assertEqual(result.exit_code, 0)
            self.assertIn("✅ Rules file is valid", log.output[0])

    @patch("unclutter_directory.unclutter_directory._load_rules")
    def test_validate_invalid_file(self, mock_load):
        mock_load.return_value = None
        
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["validate", "missing.yaml"])
        
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("File 'missing.yaml' does not exist.", result.output)

    def test_mutually_exclusive_delete_flags(self):
        rules_file = self.temp_dir / ".unclutter_rules.yaml"
        rules_file.touch()

        with self.assertLogs('unclutter_directory', level='INFO') as log:
            runner = click.testing.CliRunner()
            result = runner.invoke(cli, [
                "organize", str(self.temp_dir), "--always-delete", "--never-delete"
            ])
            
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("mutually exclusive", log.output[0])

    @patch("unclutter_directory.unclutter_directory._process_file")
    @patch("unclutter_directory.unclutter_directory._load_rules")
    def test_dry_run_execution(self, mock_load, mock_process):
        rules_file = self.temp_dir / ".unclutter_rules.yaml"
        rules_file.touch()

        mock_load.return_value = self.mock_rules

        runner = click.testing.CliRunner()
        result = runner.invoke(cli, [
            "organize", str(self.temp_dir), "--dry-run"
        ])
        
        self.assertEqual(result.exit_code, 0)
        mock_process.assert_not_called()

    @patch("unclutter_directory.unclutter_directory.ActionExecutor")
    @patch("unclutter_directory.unclutter_directory._load_rules")
    def test_rules_file_exclusion(self, mock_load, mock_executor):
        # Create test files
        rules_file = self.temp_dir / ".unclutter_rules.yaml"
        rules_file.touch()

        test_file = self.temp_dir / "data.txt"
        test_file.touch()

        mock_load.return_value = self.mock_rules

        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["organize", str(self.temp_dir)])
        
        self.assertEqual(result.exit_code, 0)
        mock_executor.return_value.execute_action.assert_called_once_with(
            test_file, self.temp_dir
        )

    @patch("unclutter_directory.unclutter_directory._load_rules")
    def test_command_aliases(self, mock_load):
        mock_load.return_value = self.mock_rules

        rules_file = self.temp_dir / "test_rules.yaml"
        rules_file.touch()
        
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["check", str(rules_file)])
        self.assertEqual(result.exit_code, 0)

        result = runner.invoke(cli, ["val", str(rules_file)])
        self.assertEqual(result.exit_code, 0)

    @patch("unclutter_directory.unclutter_directory._load_rules")
    def test_default_rules_file(self, mock_load):
        default_rules = self.temp_dir / ".unclutter_rules.yaml"
        default_rules.touch()
        mock_load.return_value = self.mock_rules

        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["organize", str(self.temp_dir)])
        
        self.assertEqual(result.exit_code, 0)
        mock_load.assert_called_with(str(default_rules))


if __name__ == "__main__":
    unittest.main()