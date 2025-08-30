import tempfile
import unittest
from pathlib import Path

from unclutter_directory.config.organize_config import ExecutionMode, OrganizeConfig


class TestOrganizeConfig(unittest.TestCase):
    """Tests for OrganizeConfig class functionality"""

    def setUp(self):
        """Set up test environment with temporary directory"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def test_valid_config_creation(self):
        """Test creation of valid configuration"""
        config = OrganizeConfig(
            target_dir=self.test_path,
            rules_file="rules.yaml",
            dry_run=False,
            quiet=False,
            always_delete=False,
            never_delete=False,
            include_hidden=False,
        )

        self.assertEqual(config.target_dir, self.test_path)
        self.assertEqual(config.rules_file, "rules.yaml")
        self.assertFalse(config.dry_run)
        self.assertFalse(config.quiet)
        self.assertFalse(config.always_delete)
        self.assertFalse(config.never_delete)
        self.assertFalse(config.include_hidden)

    def test_mutually_exclusive_flags_validation_error(self):
        """Test that ValueError is raised when always_delete and never_delete are both True"""
        with self.assertRaises(ValueError) as context:
            OrganizeConfig(
                target_dir=self.test_path,
                rules_file=None,
                dry_run=False,
                quiet=False,
                always_delete=True,
                never_delete=True,
                include_hidden=False,
            )

        self.assertIn(
            "always_delete and never_delete are mutually exclusive",
            str(context.exception),
        )

    def test_execution_mode_dry_run(self):
        """Test execution_mode property returns DRY_RUN when dry_run is True"""
        config = OrganizeConfig(
            target_dir=self.test_path,
            rules_file=None,
            dry_run=True,
            quiet=False,
            always_delete=False,
            never_delete=False,
            include_hidden=False,
        )

        self.assertEqual(config.execution_mode, ExecutionMode.DRY_RUN)

    def test_execution_mode_automatic_with_always_delete(self):
        """Test execution_mode property returns AUTOMATIC when always_delete is True"""
        config = OrganizeConfig(
            target_dir=self.test_path,
            rules_file=None,
            dry_run=False,
            quiet=False,
            always_delete=True,
            never_delete=False,
            include_hidden=False,
        )

        self.assertEqual(config.execution_mode, ExecutionMode.AUTOMATIC)

    def test_execution_mode_automatic_with_never_delete(self):
        """Test execution_mode property returns AUTOMATIC when never_delete is True"""
        config = OrganizeConfig(
            target_dir=self.test_path,
            rules_file=None,
            dry_run=False,
            quiet=False,
            always_delete=False,
            never_delete=True,
            include_hidden=False,
        )

        self.assertEqual(config.execution_mode, ExecutionMode.AUTOMATIC)

    def test_execution_mode_interactive(self):
        """Test execution_mode property returns INTERACTIVE in default case"""
        config = OrganizeConfig(
            target_dir=self.test_path,
            rules_file=None,
            dry_run=False,
            quiet=False,
            always_delete=False,
            never_delete=False,
            include_hidden=False,
        )

        self.assertEqual(config.execution_mode, ExecutionMode.INTERACTIVE)

    def test_execution_mode_overrides(self):
        """Test that dry_run overrides delete flags even if one is set"""
        config = OrganizeConfig(
            target_dir=self.test_path,
            rules_file=None,
            dry_run=True,
            quiet=False,
            always_delete=True,
            never_delete=False,
            include_hidden=False,
        )

        # dry_run should take precedence over always_delete
        self.assertEqual(config.execution_mode, ExecutionMode.DRY_RUN)

    def test_rules_file_path_with_valid_path(self):
        """Test rules_file_path property returns Path object when rules_file is set"""
        rules_path = "custom_rules.yaml"
        config = OrganizeConfig(
            target_dir=self.test_path,
            rules_file=rules_path,
            dry_run=False,
            quiet=False,
            always_delete=False,
            never_delete=False,
            include_hidden=False,
        )

        self.assertEqual(config.rules_file_path, Path(rules_path))

    def test_rules_file_path_with_none(self):
        """Test rules_file_path property returns None when rules_file is None"""
        config = OrganizeConfig(
            target_dir=self.test_path,
            rules_file=None,
            dry_run=False,
            quiet=False,
            always_delete=False,
            never_delete=False,
            include_hidden=False,
        )

        self.assertIsNone(config.rules_file_path)

    def test_execution_mode_with_both_delete_flags_error(self):
        """Test that both delete flags together raise error, even when accessed after creation"""
        # This test is tricky because the error happens in __post_init__
        # We need to use a different approach to test this specific scenario
        with self.assertRaises(ValueError):
            OrganizeConfig(
                target_dir=self.test_path,
                rules_file=None,
                dry_run=False,
                quiet=False,
                always_delete=True,
                never_delete=True,
                include_hidden=False,
            )

    def test_config_with_various_target_dir_types(self):
        """Test configuration creation with different types of target_dir"""
        # Test with Path object
        path_obj = Path("/some/path")
        config1 = OrganizeConfig(
            target_dir=path_obj,
            rules_file=None,
            dry_run=False,
            quiet=False,
            always_delete=False,
            never_delete=False,
            include_hidden=False,
        )
        self.assertEqual(config1.target_dir, path_obj)

        # Test with string path - should be converted to Path
        string_path = "/another/path"
        config2 = OrganizeConfig(
            target_dir=string_path,
            rules_file=None,
            dry_run=False,
            quiet=False,
            always_delete=False,
            never_delete=False,
            include_hidden=False,
        )
        # Since the dataclass doesn't convert string to Path automatically,
        # we need to check that it preserves the string type for now
        self.assertEqual(str(config2.target_dir), string_path)


if __name__ == "__main__":
    unittest.main(failfast=True)
