import logging
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List

import pytest

from unittest.mock import Mock
from unclutter_directory.config.organize_config import OrganizeConfig
from unclutter_directory.execution.action_executor import ActionExecutor


def create_test_structure(temp_dir: Path, structure: List[str]):
    for item in structure:
        path = temp_dir / item
        if path.suffix:  # is file
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        else:  # is directory
            path.mkdir(parents=True)


@pytest.fixture(autouse=True)
def temp_dir_setup():
    temp_dir = Path(tempfile.mkdtemp())
    test_file = temp_dir / "test_file.txt"
    test_file.touch()
    yield temp_dir, test_file
    shutil.rmtree(temp_dir)


def test_move_basic(temp_dir_setup):
    """Move file to an empty directory"""
    temp_dir, test_file = temp_dir_setup
    target = temp_dir / "target"
    action = {"type": "move", "target": str(target)}

    result = ActionExecutor(action).execute_action(test_file, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig))
    assert isinstance(result, Path)

    moved_file = target / test_file.name
    assert moved_file.exists()
    assert not test_file.exists()


def test_move_with_conflict(temp_dir_setup):
    """Move file with existing file in target"""
    temp_dir, test_file = temp_dir_setup
    target = temp_dir / "target"
    target.mkdir()
    (target / test_file.name).touch()  # Existing file

    action = {"type": "move", "target": str(target)}
    result = ActionExecutor(action).execute_action(test_file, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig))
    assert isinstance(result, Path)

    moved_file = target / "test_file_1.txt"
    assert moved_file.exists()
    assert not test_file.exists()


def test_move_absolute_path(temp_dir_setup):
    """Move using absolute path"""
    temp_dir, test_file = temp_dir_setup
    target = temp_dir / "absolute_target"
    action = {"type": "move", "target": str(target.resolve())}

    result = ActionExecutor(action).execute_action(test_file, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig))
    assert isinstance(result, Path)

    assert (target / test_file.name).exists()


def test_move_nested_directories(temp_dir_setup):
    """Move to nonexistant nested directories"""
    temp_dir, test_file = temp_dir_setup
    target = temp_dir / "nested/target/directory"
    action = {"type": "move", "target": str(target)}

    result = ActionExecutor(action).execute_action(test_file, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig))
    assert isinstance(result, Path)

    assert (target / test_file.name).exists()


def test_delete_basic(temp_dir_setup):
    """Basic delete"""
    temp_dir, test_file = temp_dir_setup
    action = {"type": "delete"}

    result = ActionExecutor(action).execute_action(test_file, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig))
    assert result is None

    assert not test_file.exists()


def test_compress_basic(temp_dir_setup):
    """Basic compression without conflicts"""
    temp_dir, test_file = temp_dir_setup
    target = temp_dir / "compressed"
    action = {"type": "compress", "target": str(target)}

    result = ActionExecutor(action).execute_action(test_file, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig))
    assert isinstance(result, Path)

    zip_file = target / "test_file.zip"
    assert zip_file.exists()
    assert not test_file.exists()  # Original must be deleted


def test_compress_with_conflict(temp_dir_setup):
    """Compress file with colliding file name"""
    temp_dir, test_file = temp_dir_setup
    target = temp_dir / "compressed"
    target.mkdir()
    (target / "test_file.zip").touch()  # Existing file

    action = {"type": "compress", "target": str(target)}
    result = ActionExecutor(action).execute_action(test_file, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig))
    assert isinstance(result, Path)

    assert (target / "test_file_1.zip").exists()


def test_compress_content_validation(temp_dir_setup):
    """Test zip content"""
    temp_dir, test_file = temp_dir_setup
    target = temp_dir / "compressed"
    content = "Test content"
    test_file.write_text(content)

    result = ActionExecutor({"type": "compress", "target": str(target)}).execute_action(
        test_file, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig)
    )
    assert isinstance(result, Path)

    with zipfile.ZipFile(target / "test_file.zip") as z:
        with z.open(test_file.name) as f:
            assert f.read().decode() == content


def test_compress_forbidden_extensions(temp_dir_setup, caplog):
    """Don't compress already compressed files"""
    temp_dir, _ = temp_dir_setup
    forbidden_files = [
        ".zip",
        ".rar",
        ".7z",
    ]
    caplog.set_level(logging.INFO)
    for ext in forbidden_files:
        file = temp_dir / f"test{ext}"
        file.touch()
        result = ActionExecutor(
            {"type": "compress", "target": str(temp_dir)}
        ).execute_action(file, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig))
        assert result is None  # Skipped, so None
        assert "Skipping compression for archive file" in caplog.text
        assert not (temp_dir / (file.name + ".zip")).exists()
        caplog.clear()


def test_compress_non_existent_directory(temp_dir_setup):
    """Compress to non existent directory"""
    temp_dir, test_file = temp_dir_setup
    target = temp_dir / "non/existent/directory"
    action = {"type": "compress", "target": str(target)}

    result = ActionExecutor(action).execute_action(test_file, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig))
    assert isinstance(result, Path)

    assert (target / "test_file.zip").exists()


def test_invalid_action(temp_dir_setup, caplog):
    """Handle malformed or unrecognized actions"""
    temp_dir, test_file = temp_dir_setup
    test_cases = [
        {"type": "move"},  # Missing target
        {"type": "invalid"},
        {"type": "compress"},  # Missing target
        {},  # Missing type
    ]
    expected_log_messages = [
        "Missing target for move action",
        "Invalid action type",
        "Missing target for compress action",
        "Invalid action type",
    ]
    caplog.set_level(logging.WARNING)
    for action, expected_msg in zip(test_cases, expected_log_messages):
        result = ActionExecutor(action).execute_action(test_file, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig))
        assert result is None
        assert expected_msg in caplog.text, (
            f"Expected message '{expected_msg}' not found in logs"
        )
        caplog.clear()


def test_move_error_handling(temp_dir_setup, mocker, caplog):
    """Error handling during movement"""
    temp_dir, test_file = temp_dir_setup
    mock_move = mocker.patch("shutil.move")
    mock_move.side_effect = Exception("Simulated error")
    action = {"type": "move", "target": str(temp_dir / "target")}

    result = ActionExecutor(action).execute_action(test_file, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig))
    assert result is None
    assert "Unexpected error processing" in caplog.text


def test_delete_error_handling(temp_dir_setup, monkeypatch, caplog):
    """Error handling during delete"""
    temp_dir, test_file = temp_dir_setup

    def mock_unlink(*args, **kwargs):
        raise Exception("Simulated error")

    monkeypatch.setattr(Path, "unlink", mock_unlink)
    result = ActionExecutor({"type": "delete"}).execute_action(test_file, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig))
    assert result is None
    assert "Error deleting " in caplog.text


def test_delete_directory(temp_dir_setup):
    """Delete directory with nested content"""
    temp_dir, _ = temp_dir_setup
    test_dir = temp_dir / "test_dir"
    create_test_structure(temp_dir, ["test_dir/file1.txt", "test_dir/subdir/file2.txt"])

    result = ActionExecutor({"type": "delete"}).execute_action(test_dir, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig))
    assert result is None
    assert not test_dir.exists()


def test_compress_directory(temp_dir_setup):
    """Compress directory with nested structure"""
    temp_dir, _ = temp_dir_setup
    test_dir = temp_dir / "to_compress"
    create_test_structure(
        temp_dir, ["to_compress/file.txt", "to_compress/subdir/nested.txt"]
    )

    result = ActionExecutor({"type": "compress", "target": "archives"}).execute_action(
        test_dir, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig)
    )
    assert isinstance(result, Path)

    zip_path = temp_dir / "archives" / "to_compress.zip"
    with zipfile.ZipFile(zip_path) as z:
        assert "to_compress/file.txt" in z.namelist()
        assert "to_compress/subdir/nested.txt" in z.namelist()
    assert not test_dir.exists()


def test_compress_directory_conflict(temp_dir_setup):
    """Handle directory compression naming conflicts"""
    temp_dir, _ = temp_dir_setup
    target = temp_dir / "archives"
    target.mkdir()
    (target / "test_dir.zip").touch()

    test_dir = temp_dir / "test_dir"
    test_dir.mkdir()

    result = ActionExecutor({"type": "compress", "target": "archives"}).execute_action(
        test_dir, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig)
    )
    assert isinstance(result, Path)
    assert (target / "test_dir_1.zip").exists()


def test_move_directory(temp_dir_setup):
    """Move directory with contents"""
    temp_dir, _ = temp_dir_setup
    test_dir = temp_dir / "source"
    create_test_structure(temp_dir, ["source/data.txt"])

    result = ActionExecutor({"type": "move", "target": "dest"}).execute_action(
        test_dir, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig)
    )
    assert isinstance(result, Path)

    moved = temp_dir / "dest" / "source"
    assert moved.exists()
    assert (moved / "data.txt").exists()
    assert not test_dir.exists()


def test_compress_directory_with_archives(temp_dir_setup):
    """Compress directory containing archive files"""
    temp_dir, _ = temp_dir_setup
    test_dir = temp_dir / "mixed"
    create_test_structure(temp_dir, ["mixed/data.zip", "mixed/backup.rar"])

    result = ActionExecutor({"type": "compress", "target": "output"}).execute_action(
        test_dir, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig)
    )
    assert isinstance(result, Path)

    with zipfile.ZipFile(temp_dir / "output" / "mixed.zip") as z:
        assert "mixed/data.zip" in z.namelist()


def test_directory_name_with_archive_extension(temp_dir_setup):
    """Compress directory named like an archive file"""
    temp_dir, _ = temp_dir_setup
    test_dir = temp_dir / "fake.zip"
    test_dir.mkdir()
    (test_dir / "file.txt").touch()

    result = ActionExecutor({"type": "compress", "target": "output"}).execute_action(
        test_dir, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig)
    )
    assert isinstance(result, Path)
    assert (temp_dir / "output" / "fake.zip.zip").exists()


def test_empty_directory_compression(temp_dir_setup):
    """Compress empty directory"""
    temp_dir, _ = temp_dir_setup
    test_dir = temp_dir / "empty"
    test_dir.mkdir()

    result = ActionExecutor({"type": "compress", "target": "archives"}).execute_action(
        test_dir, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig)
    )
    assert isinstance(result, Path)
    zip_path = temp_dir / "archives" / "empty.zip"
    assert zip_path.exists()


def test_compress_directory_with_empty_subdirectory(temp_dir_setup):
    """Compress directory containing an empty subdirectory"""
    temp_dir, _ = temp_dir_setup
    test_dir = temp_dir / "dir"
    create_test_structure(
        temp_dir,
        [
            "dir/empty/",
        ],
    )

    result = ActionExecutor({"type": "compress", "target": "output"}).execute_action(
        test_dir, temp_dir, {"delete_unpacked_on_match": False}, Mock(spec=OrganizeConfig)
    )
    assert isinstance(result, Path)

    with zipfile.ZipFile(temp_dir / "output" / "dir.zip") as z:
        assert "dir/empty/" in z.namelist()
