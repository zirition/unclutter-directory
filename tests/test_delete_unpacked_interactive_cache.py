import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from unclutter_directory.commands.delete_unpacked_command import DeleteUnpackedCommand
from unclutter_directory.config.delete_unpacked_config import DeleteUnpackedConfig


def test_delete_unpacked_interactive_cache_all():
    """Test that 'all' response is cached and reused in delete-unpacked command"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test archives and directories
        # Archive 1 and directory 1
        archive1_path = temp_path / "test1.zip"
        dir1_path = temp_path / "test1"
        dir1_path.mkdir()
        (dir1_path / "file1.txt").write_text("content1")

        with zipfile.ZipFile(archive1_path, "w") as zf:
            zf.writestr("file1.txt", "content1")

        # Archive 2 and directory 2
        archive2_path = temp_path / "test2.zip"
        dir2_path = temp_path / "test2"
        dir2_path.mkdir()
        (dir2_path / "file2.txt").write_text("content2")

        with zipfile.ZipFile(archive2_path, "w") as zf:
            zf.writestr("file2.txt", "content2")

        # Create config for interactive mode
        config = DeleteUnpackedConfig(
            target_dir=temp_path,
            always_delete=False,
            never_delete=False,
            include_hidden=False,
            quiet=True,
        )

        command = DeleteUnpackedCommand(config)

        # Mock the input to return 'a' (all) on the first call, and check that it's not called again
        input_calls = []

        def mock_input(prompt):
            input_calls.append(prompt)
            return "a"  # Always respond with 'all'

        with patch("builtins.input", side_effect=mock_input):
            command.execute()

        # Should only ask once, even though there are two identical pairs
        assert len(input_calls) == 1

        # Verify directories were deleted
        assert not dir1_path.exists()
        assert not dir2_path.exists()


def test_delete_unpacked_interactive_cache_never():
    """Test that 'never' response is cached and reused in delete-unpacked command"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test archives and directories
        # Archive 1 and directory 1
        archive1_path = temp_path / "test1.zip"
        dir1_path = temp_path / "test1"
        dir1_path.mkdir()
        (dir1_path / "file1.txt").write_text("content1")

        with zipfile.ZipFile(archive1_path, "w") as zf:
            zf.writestr("file1.txt", "content1")

        # Archive 2 and directory 2
        archive2_path = temp_path / "test2.zip"
        dir2_path = temp_path / "test2"
        dir2_path.mkdir()
        (dir2_path / "file2.txt").write_text("content2")

        with zipfile.ZipFile(archive2_path, "w") as zf:
            zf.writestr("file2.txt", "content2")

        # Create config for interactive mode
        config = DeleteUnpackedConfig(
            target_dir=temp_path,
            always_delete=False,
            never_delete=False,
            include_hidden=False,
            quiet=True,
        )

        command = DeleteUnpackedCommand(config)

        # Mock the input to return 'never' on the first call, and check that it's not called again
        input_calls = []

        def mock_input(prompt):
            input_calls.append(prompt)
            return "never"  # Always respond with 'never'

        with patch("builtins.input", side_effect=mock_input):
            command.execute()

        # Should only ask once, even though there are two identical pairs
        assert len(input_calls) == 1

        # Verify directories were not deleted
        assert dir1_path.exists()
        assert dir2_path.exists()


if __name__ == "__main__":
    pytest.main([__file__])
