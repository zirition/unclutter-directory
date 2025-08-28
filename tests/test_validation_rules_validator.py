import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile

from unclutter_directory.validation.rules_validator import RulesFileValidator
from unclutter_directory.config.organize_config import OrganizeConfig


class TestRulesFileValidator(unittest.TestCase):
    def setUp(self):
        self.validator = RulesFileValidator()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.target_dir = Path(self.temp_dir.name)

    def make_config(self, rules_file=None):
        return OrganizeConfig(
            target_dir=self.target_dir,
            rules_file=rules_file,
            dry_run=False,
            quiet=False,
            always_delete=False,
            never_delete=False,
            include_hidden=False,
        )

    def test_no_rules_file_and_no_default(self):
        config = self.make_config(rules_file=None)
        # No default file created
        errors = self.validator.validate(config)
        self.assertIn("No rules file specified and no default .unclutter_rules.yaml found in target directory", errors)

    def test_rules_file_not_exist(self):
        config = self.make_config(rules_file="/nonexistent.yaml")
        errors = self.validator.validate(config)
        self.assertTrue(any("does not exist" in e for e in errors))

    @patch("pathlib.Path.is_file", return_value=False)
    def test_rules_file_not_regular_file(self, mock_is_file):
        # Create default file with invalid YAML content
        default_file = self.target_dir / ".unclutter_rules.yaml"
        default_file.write_text("invalid: [unclosed")
        config = self.make_config(rules_file=str(default_file))
        errors = self.validator.validate(config)
        self.assertTrue(any("not a regular file" in e for e in errors))

    @patch("pathlib.Path.stat")
    def test_rules_file_too_large(self, mock_stat):
        mock_stat.return_value.st_size = 11 * 1024 * 1024  # 11MB
        config = self.make_config(rules_file="/some/path.yaml")
        with patch("pathlib.Path.exists", return_value=True), patch("pathlib.Path.is_file", return_value=True):
            errors = self.validator.validate(config)
        self.assertTrue(any("too large" in e for e in errors))

    @patch("pathlib.Path.stat")
    def test_rules_file_empty(self, mock_stat):
        mock_stat.return_value.st_size = 0
        config = self.make_config(rules_file="/some/path.yaml")
        with patch("pathlib.Path.exists", return_value=True), patch("pathlib.Path.is_file", return_value=True):
            errors = self.validator.validate(config)
        self.assertTrue(any("empty" in e for e in errors))

    @patch("pathlib.Path.stat")
    def test_rules_file_not_readable(self, mock_stat):
        # No read permission bit set
        mock_stat.return_value.st_size = 100
        mock_stat.return_value.st_mode = 0o200  # write only
        config = self.make_config(rules_file="/some/path.yaml")
        with patch("pathlib.Path.exists", return_value=True), patch("pathlib.Path.is_file", return_value=True):
            errors = self.validator.validate(config)
        self.assertTrue(any("not readable" in e for e in errors))

    def test_load_rules_invalid_yaml(self):
        config = self.make_config(rules_file=None)
        # Create default file with invalid YAML content
        default_file = self.target_dir / ".unclutter_rules.yaml"
        default_file.write_text("invalid: [unclosed")
        config.rules_file = str(default_file)
        with patch("pathlib.Path.exists", return_value=True), patch("pathlib.Path.is_file", return_value=True), \
             patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value.st_size = len(default_file.read_text())
            mock_stat.return_value.st_mode = 0o400
            errors = self.validator.validate(config)
        self.assertTrue(any("Failed to load rules" in e or "Unexpected error" in e for e in errors))

    def test_load_rules_empty_or_not_list(self):
        config = self.make_config(rules_file=None)
        default_file = self.target_dir / ".unclutter_rules.yaml"
        default_file.write_text("")  # empty file
        config.rules_file = str(default_file)
        with patch("pathlib.Path.exists", return_value=True), patch("pathlib.Path.is_file", return_value=True), \
             patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value.st_size = 1
            mock_stat.return_value.st_mode = 0o400
            errors = self.validator.validate(config)
        self.assertTrue(any("Failed to load rules" in e for e in errors))

        # Write non-list YAML content
        default_file.write_text("key: value")
        with patch("pathlib.Path.exists", return_value=True), patch("pathlib.Path.is_file", return_value=True), \
             patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value.st_size = len(default_file.read_text())
            mock_stat.return_value.st_mode = 0o400
            errors = self.validator.validate(config)
        self.assertTrue(any("Failed to load rules" in e for e in errors))

    @patch("unclutter_directory.commons.validate_rules_file")
    def test_rules_file_with_validation_errors(self, mock_validate_rules_file):
        config = self.make_config(rules_file=None)
        default_file = self.target_dir / ".unclutter_rules.yaml"
        # Add a condition with invalid size value
        default_file.write_text("- name: rule1\n  conditions:\n    larger: 100s\n  action:\n    type: move\n    target: /dest")
        config.rules_file = str(default_file)
        mock_validate_rules_file.return_value = ["Error in rule"]
        with patch("pathlib.Path.exists", return_value=True), patch("pathlib.Path.is_file", return_value=True), \
             patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value.st_size = len(default_file.read_text())
            mock_stat.return_value.st_mode = 0o400
            errors = self.validator.validate(config)
        self.assertTrue(any("Invalid size value" in e for e in errors))

    def test_exceptions_handling(self):
        config = self.make_config(rules_file="/some/path.yaml")
        with patch("pathlib.Path.exists", side_effect=MemoryError):
            with self.assertRaises(MemoryError):
                self.validator.validate(config)

        with patch("pathlib.Path.exists", side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                self.validator.validate(config)

        with patch("pathlib.Path.exists", side_effect=OSError("os error")):
            with self.assertRaises(OSError):
                self.validator.validate(config)

        with patch("pathlib.Path.exists", side_effect=Exception("unexpected")):
            with self.assertRaises(Exception):
                self.validator.validate(config)


if __name__ == "__main__":
    unittest.main()