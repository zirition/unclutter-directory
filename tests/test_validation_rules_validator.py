import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from unclutter_directory.config.organize_config import OrganizeConfig
from unclutter_directory.validation.rules_validator import RulesFileValidator


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
        self.assertIn(
            "No rules file specified and no default .unclutter_rules.yaml found in target directory",
            errors,
        )

    def test_rules_file_not_exist(self):
        config = self.make_config(rules_file="/nonexistent.yaml")
        errors = self.validator.validate(config)
        self.assertTrue(any("does not exist" in e for e in errors))

    def test_rules_file_is_directory(self):
        # Test with a directory path
        config = self.make_config(rules_file=str(self.target_dir))
        errors = self.validator.validate(config)
        self.assertTrue(any("not a regular file" in e for e in errors))

    def test_rules_file_too_large(self):
        # Create a temporary file larger than 10MB limit
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"0" * (11 * 1024 * 1024))  # 11MB
            large_file_path = f.name
        try:
            config = self.make_config(rules_file=large_file_path)
            errors = self.validator.validate(config)
            self.assertTrue(any("too large" in e for e in errors))
        finally:
            Path(large_file_path).unlink(missing_ok=True)

    def test_rules_file_empty(self):
        # Create an empty temporary file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            empty_file_path = f.name
        try:
            config = self.make_config(rules_file=empty_file_path)
            errors = self.validator.validate(config)
            self.assertTrue(any("empty" in e for e in errors))
        finally:
            Path(empty_file_path).unlink(missing_ok=True)

    def test_rules_file_not_readable(self):
        # Create a temporary file with no read permissions
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"some content")
            no_read_file = f.name
        os.chmod(no_read_file, 0o200)  # write only
        try:
            config = self.make_config(rules_file=no_read_file)
            errors = self.validator.validate(config)
            self.assertTrue(any("not readable" in e for e in errors))
        finally:
            os.chmod(no_read_file, 0o600)  # restore read permission to allow deletion
            Path(no_read_file).unlink(missing_ok=True)

    def test_load_rules_invalid_yaml(self):
        # Create default file with invalid YAML content
        default_file = self.target_dir / ".unclutter_rules.yaml"
        default_file.write_text("invalid: [unclosed")
        config = self.make_config(rules_file=None)  # Will auto-detect default file
        errors = self.validator.validate(config)
        self.assertTrue(
            any("Failed to load rules" in e or "Unexpected error" in e for e in errors)
        )

    def test_load_rules_empty_or_not_list(self):
        # Test empty file with whitespace
        config = self.make_config(rules_file=None)
        default_file = self.target_dir / ".unclutter_rules.yaml"
        default_file.write_text("   ")  # whitespace only, triggers internal empty check
        config.rules_file = str(default_file)
        errors = self.validator.validate(config)
        self.assertTrue(any("Failed to load rules" in e for e in errors))

        # Test non-list content
        default_file.write_text("key: value")
        config.rules_file = str(default_file)
        errors = self.validator.validate(config)
        self.assertTrue(any("Failed to load rules" in e for e in errors))

    @patch("unclutter_directory.commons.validate_rules_file")
    def test_rules_file_with_validation_errors(self, mock_validate_rules_file):
        config = self.make_config(rules_file=None)
        default_file = self.target_dir / ".unclutter_rules.yaml"
        # Add a condition with invalid size value
        default_file.write_text(
            "- name: rule1\n  conditions:\n    larger: 100s\n  action:\n    type: move\n    target: /dest"
        )
        config.rules_file = str(default_file)
        mock_validate_rules_file.return_value = ["Invalid size value"]
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

        with patch("pathlib.Path.exists", side_effect=ValueError("unexpected")):
            with self.assertRaises(ValueError):
                self.validator.validate(config)


if __name__ == "__main__":
    unittest.main()
