import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from unclutter_directory.file_operations.file_collector import FileCollector


def test_collect_basic():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir)
        file1 = test_path / "file1.txt"
        file1.write_text("content1")
        file2 = test_path / ".hiddenfile"
        file2.write_text("hidden content")

        collector = FileCollector(include_hidden=False)
        collected = collector.collect(test_path)
        assert file1 in collected
        assert file2 not in collected


def test_collect_include_hidden():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir)
        file1 = test_path / "file1.txt"
        file1.write_text("content1")
        file2 = test_path / ".hiddenfile"
        file2.write_text("hidden content")

        collector = FileCollector(include_hidden=True)
        collected = collector.collect(test_path)
        assert file1 in collected
        assert file2 in collected


def test_collect_includes_all_files():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir)
        file1 = test_path / "file1.txt"
        file1.write_text("content1")
        rules_file = test_path / "rules.yaml"
        rules_file.write_text("rules content")

        collector = FileCollector()
        collected = collector.collect(test_path)
        assert file1 in collected
        assert rules_file in collected


def test_collect_permission_error():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir)
        collector = FileCollector()
        with patch.object(Path, "iterdir", side_effect=PermissionError):
            with pytest.raises(PermissionError):
                collector.collect(test_path)


def test_collect_os_error():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir)
        collector = FileCollector()
        with patch.object(Path, "iterdir", side_effect=OSError("fail")):
            with pytest.raises(OSError):
                collector.collect(test_path)


def test_collect_recursive_depth_1():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir)
        file1 = test_path / "file1.txt"
        file1.write_text("content1")
        subdir = test_path / "subdir"
        subdir.mkdir()
        file2 = subdir / "file2.txt"
        file2.write_text("content2")

        collector = FileCollector()
        collected = collector.collect_recursive(test_path, max_depth=1)
        assert file1 in collected
        assert subdir in collected
        assert file2 not in collected


def test_collect_recursive_depth_2():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir)
        file1 = test_path / "file1.txt"
        file1.write_text("content1")
        subdir = test_path / "subdir"
        subdir.mkdir()
        file2 = subdir / "file2.txt"
        file2.write_text("content2")

        collector = FileCollector()
        collected = collector.collect_recursive(test_path, max_depth=2)
        assert file1 in collected
        assert subdir in collected
        assert file2 in collected


def test_collect_recursive_depth_0():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir)
        collector = FileCollector()
        collected = collector.collect_recursive(test_path, max_depth=0)
        assert collected == []


def test_collect_empty_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir)
        collector = FileCollector()
        collected = collector.collect(test_path)
        assert collected == []


def test_collect_only_hidden_files():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir)
        hidden_file = test_path / ".hiddenfile"
        hidden_file.write_text("hidden content")
        collector = FileCollector(include_hidden=False)
        collected = collector.collect(test_path)
        assert collected == []
        collector_include = FileCollector(include_hidden=True)
        collected_include = collector_include.collect(test_path)
        assert hidden_file in collected_include


def test_collect_with_symbolic_link():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir)
        # Create a real file and a symlink to it
        target_file = test_path / "target.txt"
        target_file.write_text("target content")
        symlink = test_path / "symlink.txt"
        try:
            symlink.symlink_to(target_file)
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks not supported on this platform")
        collector = FileCollector()
        collected = collector.collect(test_path)
        assert target_file in collected
        assert symlink in collected


def test_collect_recursive_deeper_than_max_depth():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir)
        # Create nested directories deeper than max_depth
        current_dir = test_path
        for i in range(5):
            current_dir = current_dir / f"dir{i}"
            current_dir.mkdir()
            (current_dir / f"file{i}.txt").write_text(f"content{i}")
        collector = FileCollector()
        collected = collector.collect_recursive(test_path, max_depth=3)

        # Directories deeper than depth 3 should not be included
        current_dir = test_path
        for i in range(3):
            current_dir = current_dir / f"dir{i}"
            assert current_dir in collected
        for i in range(3, 5):
            current_dir = current_dir / f"dir{i}"
            assert current_dir not in collected

        # Files in directory 3 are in depth 4
        current_dir = test_path
        for i in range(2):
            current_dir = current_dir / f"dir{i}"
            assert current_dir / f"file{i}.txt" in collected
        for i in range(2, 5):
            current_dir = current_dir / f"dir{i}"
            assert current_dir / f"file{i}.txt" not in collected


def test_collect_files_with_unusual_names():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir)
        filenames = [
            "file with spaces.txt",
            "unicodé_файл.txt",
            "special_!@#$%^&*().txt",
            "1234567890.txt",
        ]
        for name in filenames:
            (test_path / name).write_text("content")
        collector = FileCollector()
        collected = collector.collect(test_path)
        for name in filenames:
            assert test_path / name in collected


def test_collect_with_nonexistent_file_reference():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir)
        file1 = test_path / "file1.txt"
        file1.write_text("content1")
        collector = FileCollector()
        collected = collector.collect(test_path)
        assert file1 in collected


def test_collect_with_file_path_instead_of_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir)
        file1 = test_path / "file1.txt"
        file1.write_text("content1")
        collector = FileCollector()
        with pytest.raises(NotADirectoryError):
            collector.collect(file1)


def test_collect_nonexistent_path():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = Path(temp_dir)
        collector = FileCollector()
        nonexistent_path = test_path / "does_not_exist"
        with pytest.raises(FileNotFoundError):
            collector.collect(nonexistent_path)
