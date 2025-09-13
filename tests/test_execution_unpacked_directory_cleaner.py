"""
Tests for the UnpackedDirectoryCleaner class.
"""

import logging
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from unclutter_directory.config.organize_config import ExecutionMode, OrganizeConfig
from unclutter_directory.execution.unpacked_directory_cleaner import (
    UnpackedDirectoryCleaner,
)


class TestUnpackedDirectoryCleaner:
    """Test suite for UnpackedDirectoryCleaner."""

    @pytest.fixture
    def mock_config_always_delete(self):
        """Mock config with always_delete=True."""
        config = Mock(spec=OrganizeConfig)
        config.always_delete = True
        config.dry_run = False
        config.include_hidden = False
        config.never_delete = False
        config.execution_mode = ExecutionMode.AUTOMATIC
        return config

    @pytest.fixture
    def mock_config_dry_run(self):
        """Mock config with dry_run=True."""
        config = Mock(spec=OrganizeConfig)
        config.always_delete = False
        config.dry_run = True
        config.include_hidden = False
        config.never_delete = False
        config.execution_mode = ExecutionMode.DRY_RUN
        return config

    def setup_temp_files(
        self, temp_parent: str, stem: str = "original", identical: bool = True
    ):
        """Setup temporary archive and directory."""
        original_path = Path(temp_parent) / f"{stem}.zip"
        final_path = Path(temp_parent) / "final.zip"

        # Create original and final archive with same content
        content = b"test content"
        with zipfile.ZipFile(original_path, "w") as z:
            z.writestr("test.txt", content)
        with zipfile.ZipFile(final_path, "w") as z:
            z.writestr("test.txt", content)

        # Create expected directory
        expected_dir = Path(temp_parent) / stem
        expected_dir.mkdir()
        (expected_dir / "test.txt").write_bytes(content)

        if not identical:
            # Add extra file to make not identical
            (expected_dir / "extra.txt").write_text("extra")

        return original_path, final_path, expected_dir

    def test_clean_success(self, mock_config_always_delete, caplog):
        """Test successful cleaning when directory is identical and should be deleted."""
        caplog.set_level(logging.INFO)
        cleaner = UnpackedDirectoryCleaner(mock_config_always_delete)

        with tempfile.TemporaryDirectory() as temp_parent:
            original_path, final_path, expected_dir = self.setup_temp_files(temp_parent)

            cleaner.clean(original_path, final_path)

            assert "Checking for unpacked directory to clean" in caplog.text
            assert "Comparing archive" in caplog.text
            assert "Archive and directory are identical" in caplog.text
            assert "Proceeding with deletion" in caplog.text
            assert "✅ Deleted duplicate directory" in caplog.text
            assert not expected_dir.exists()

    def test_clean_not_identical(self, mock_config_always_delete, caplog):
        """Test when archive and directory are not identical."""
        caplog.set_level(logging.INFO)
        cleaner = UnpackedDirectoryCleaner(mock_config_always_delete)

        with tempfile.TemporaryDirectory() as temp_parent:
            original_path, final_path, expected_dir = self.setup_temp_files(
                temp_parent, identical=False
            )

            cleaner.clean(original_path, final_path)

            assert "Archive and directory are not identical" in caplog.text
            assert "Extra in directory: extra.txt" in caplog.text
            assert expected_dir.exists()

    def test_clean_dir_not_found(self, mock_config_always_delete, caplog):
        """Test when unpacked directory does not exist."""
        caplog.set_level(logging.DEBUG)
        cleaner = UnpackedDirectoryCleaner(mock_config_always_delete)

        with tempfile.TemporaryDirectory() as temp_parent:
            original_path = Path(temp_parent) / "original.zip"
            final_path = Path(temp_parent) / "final.zip"

            # Create archives but no directory
            with zipfile.ZipFile(original_path, "w") as z:
                z.writestr("test.txt", b"content")
            with zipfile.ZipFile(final_path, "w") as z:
                z.writestr("test.txt", b"content")

            expected_dir = Path(temp_parent) / "original"

            cleaner.clean(original_path, final_path)

            assert "Checking for unpacked directory to clean" in caplog.text
            assert "Unpacked directory not found" in caplog.text
            assert not expected_dir.exists()

    def test_clean_dry_run(self, mock_config_dry_run, caplog):
        """Test cleaning in dry_run mode."""
        caplog.set_level(logging.INFO)
        cleaner = UnpackedDirectoryCleaner(mock_config_dry_run)

        with tempfile.TemporaryDirectory() as temp_parent:
            original_path, final_path, expected_dir = self.setup_temp_files(temp_parent)

            cleaner.clean(original_path, final_path)

            assert "Checking for unpacked directory to clean" in caplog.text
            assert "Comparing archive" in caplog.text
            assert "Archive and directory are identical" in caplog.text
            assert "Deletion skipped for" in caplog.text
            assert expected_dir.exists()
