import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

from unclutter_directory.commands.delete_unpacked_command import DeleteUnpackedCommand
from unclutter_directory.comparison.archive_directory_comparator import ComparisonResult
from unclutter_directory.config.delete_unpacked_config import DeleteUnpackedConfig


def test_delete_unpacked_no_pairs(caplog):
    """Test when no potential pairs are found."""
    caplog.set_level("INFO")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config = DeleteUnpackedConfig(target_dir=temp_path, quiet=False)
        command = DeleteUnpackedCommand(config)

        with patch.object(
            command.comparator, "find_potential_duplicates", return_value=[]
        ):
            command.execute()

        assert "No potential archive-directory duplicates found" in caplog.text


def test_delete_unpacked_never_delete_simulates(caplog):
    """Test never_delete mode simulates deletion without executing."""
    caplog.set_level("INFO")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create archive and directory
        archive_path = temp_path / "test.zip"
        dir_path = temp_path / "test"
        dir_path.mkdir()
        (dir_path / "file.txt").write_text("content")

        with zipfile.ZipFile(archive_path, "w") as z:
            z.writestr("file.txt", "content")

        # Config with never_delete
        config = DeleteUnpackedConfig(
            target_dir=temp_path,
            never_delete=True,
            quiet=False,
        )
        command = DeleteUnpackedCommand(config)

        # Mock comparator
        with patch.object(command.comparator, "find_potential_duplicates") as mock_find:
            mock_find.return_value = [(archive_path, dir_path)]
            with patch.object(
                command.comparator, "compare_archive_and_directory"
            ) as mock_compare:
                mock_result = ComparisonResult(
                    archive_path=archive_path,
                    directory_path=dir_path,
                    archive_files=[("file.txt", b"content")],
                    directory_files=[("file.txt", b"content")],
                    identical=True,
                    differences=[],
                )
                mock_compare.return_value = mock_result
                with patch(
                    "unclutter_directory.commands.delete_unpacked_command.shutil.rmtree"
                ) as mock_rmtree:
                    command.execute()

                # Verify no deletion
                mock_rmtree.assert_not_called()
                assert dir_path.exists()

                # Check dry-run log
                expected_log = "[DRY RUN] Would delete for directory 'test' (identical to 'test.zip')"
                assert expected_log in caplog.text


def test_delete_unpacked_always_delete_deletes(caplog):
    """Test always_delete mode deletes without prompting."""
    caplog.set_level("INFO")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create archive and directory
        archive_path = temp_path / "test.zip"
        dir_path = temp_path / "test"
        dir_path.mkdir()
        (dir_path / "file.txt").write_text("content")

        with zipfile.ZipFile(archive_path, "w") as z:
            z.writestr("file.txt", "content")

        # Config with always_delete
        config = DeleteUnpackedConfig(
            target_dir=temp_path,
            always_delete=True,
            quiet=False,
        )
        command = DeleteUnpackedCommand(config)

        # Mock comparator
        with patch.object(command.comparator, "find_potential_duplicates") as mock_find:
            mock_find.return_value = [(archive_path, dir_path)]
            with patch.object(
                command.comparator, "compare_archive_and_directory"
            ) as mock_compare:
                mock_result = ComparisonResult(
                    archive_path=archive_path,
                    directory_path=dir_path,
                    archive_files=[("file.txt", b"content")],
                    directory_files=[("file.txt", b"content")],
                    identical=True,
                    differences=[],
                )
                mock_compare.return_value = mock_result
                with patch(
                    "unclutter_directory.commands.delete_unpacked_command.shutil.rmtree"
                ) as mock_rmtree:
                    command.execute()

                # Verify deletion
                mock_rmtree.assert_called_once_with(dir_path)
                # Since mock is used, the file still exists, but call was made

                # No dry-run log, but info logs present
                assert "Structures are identical" in caplog.text


def test_delete_unpacked_interactive_confirms(caplog):
    """Test interactive mode with user confirmation."""
    caplog.set_level("INFO")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create archive and directory
        archive_path = temp_path / "test.zip"
        dir_path = temp_path / "test"
        dir_path.mkdir()
        (dir_path / "file.txt").write_text("content")

        with zipfile.ZipFile(archive_path, "w") as z:
            z.writestr("file.txt", "content")

        # Default config (interactive)
        config = DeleteUnpackedConfig(
            target_dir=temp_path,
            quiet=False,
        )
        command = DeleteUnpackedCommand(config)

        # Mock comparator and input
        with patch.object(command.comparator, "find_potential_duplicates") as mock_find:
            mock_find.return_value = [(archive_path, dir_path)]
            with patch.object(
                command.comparator, "compare_archive_and_directory"
            ) as mock_compare:
                mock_result = ComparisonResult(
                    archive_path=archive_path,
                    directory_path=dir_path,
                    archive_files=[("file.txt", b"content")],
                    directory_files=[("file.txt", b"content")],
                    identical=True,
                    differences=[],
                )
                mock_compare.return_value = mock_result
                with patch("builtins.input", return_value="y"):
                    with patch(
                        "unclutter_directory.commands.delete_unpacked_command.shutil.rmtree"
                    ) as mock_rmtree:
                        command.execute()

                # Verify deletion on yes
                mock_rmtree.assert_called_once_with(dir_path)
                # Since mock is used, the file still exists, but call was made


def test_delete_unpacked_interactive_skips(caplog):
    """Test interactive mode skips on user denial."""
    caplog.set_level("INFO")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create archive and directory
        archive_path = temp_path / "test.zip"
        dir_path = temp_path / "test"
        dir_path.mkdir()
        (dir_path / "file.txt").write_text("content")

        with zipfile.ZipFile(archive_path, "w") as z:
            z.writestr("file.txt", "content")

        # Default config (interactive)
        config = DeleteUnpackedConfig(
            target_dir=temp_path,
            quiet=False,
        )
        command = DeleteUnpackedCommand(config)

        # Mock comparator and input
        with patch.object(command.comparator, "find_potential_duplicates") as mock_find:
            mock_find.return_value = [(archive_path, dir_path)]
            with patch.object(
                command.comparator, "compare_archive_and_directory"
            ) as mock_compare:
                mock_result = ComparisonResult(
                    archive_path=archive_path,
                    directory_path=dir_path,
                    archive_files=[("file.txt", b"content")],
                    directory_files=[("file.txt", b"content")],
                    identical=True,
                    differences=[],
                )
                mock_compare.return_value = mock_result
                with patch("builtins.input", return_value="n"):
                    with patch(
                        "unclutter_directory.commands.delete_unpacked_command.shutil.rmtree"
                    ) as mock_rmtree:
                        command.execute()

                # Verify no deletion
                mock_rmtree.assert_not_called()
                assert dir_path.exists()
                assert "Skipping deletion of test" in caplog.text
