import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from unclutter_directory.file_operations.file_collector import FileCollector

class TestFileCollector(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_collect_basic(self):
        file1 = self.test_path / "file1.txt"
        file1.write_text("content1")
        file2 = self.test_path / ".hiddenfile"
        file2.write_text("hidden content")

        collector = FileCollector(include_hidden=False)
        collected = collector.collect(self.test_path)
        self.assertIn(file1, collected)
        self.assertNotIn(file2, collected)

    def test_collect_include_hidden(self):
        file1 = self.test_path / "file1.txt"
        file1.write_text("content1")
        file2 = self.test_path / ".hiddenfile"
        file2.write_text("hidden content")

        collector = FileCollector(include_hidden=True)
        collected = collector.collect(self.test_path)
        self.assertIn(file1, collected)
        self.assertIn(file2, collected)

    def test_collect_exclude_rules_file(self):
        file1 = self.test_path / "file1.txt"
        file1.write_text("content1")
        rules_file = self.test_path / "rules.yaml"
        rules_file.write_text("rules content")

        collector = FileCollector()
        collected = collector.collect(self.test_path, rules_file_path=rules_file)
        self.assertIn(file1, collected)
        self.assertNotIn(rules_file, collected)

    def test_collect_permission_error(self):
        collector = FileCollector()
        with patch.object(Path, "iterdir", side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                collector.collect(self.test_path)

    def test_collect_generic_exception(self):
        collector = FileCollector()
        with patch.object(Path, "iterdir", side_effect=Exception("fail")):
            with self.assertRaises(Exception):
                collector.collect(self.test_path)

    def test_collect_recursive_depth_1(self):
        file1 = self.test_path / "file1.txt"
        file1.write_text("content1")
        subdir = self.test_path / "subdir"
        subdir.mkdir()
        file2 = subdir / "file2.txt"
        file2.write_text("content2")

        collector = FileCollector()
        collected = collector.collect_recursive(self.test_path, max_depth=1)
        self.assertIn(file1, collected)
        self.assertIn(subdir, collected)
        self.assertNotIn(file2, collected)

    def test_collect_recursive_depth_2(self):
        file1 = self.test_path / "file1.txt"
        file1.write_text("content1")
        subdir = self.test_path / "subdir"
        subdir.mkdir()
        file2 = subdir / "file2.txt"
        file2.write_text("content2")

        collector = FileCollector()
        collected = collector.collect_recursive(self.test_path, max_depth=2)
        self.assertIn(file1, collected)
        self.assertIn(subdir, collected)
        self.assertIn(file2, collected)

    def test_collect_recursive_depth_0(self):
        collector = FileCollector()
        collected = collector.collect_recursive(self.test_path, max_depth=0)
        self.assertEqual(collected, [])


    def test_collect_empty_directory(self):
        collector = FileCollector()
        collected = collector.collect(self.test_path)
        self.assertEqual(collected, [])

    def test_collect_only_hidden_files(self):
        hidden_file = self.test_path / ".hiddenfile"
        hidden_file.write_text("hidden content")
        collector = FileCollector(include_hidden=False)
        collected = collector.collect(self.test_path)
        self.assertEqual(collected, [])
        collector_include = FileCollector(include_hidden=True)
        collected_include = collector_include.collect(self.test_path)
        self.assertIn(hidden_file, collected_include)

    def test_collect_with_symbolic_link(self):
        # Create a real file and a symlink to it
        target_file = self.test_path / "target.txt"
        target_file.write_text("target content")
        symlink = self.test_path / "symlink.txt"
        try:
            symlink.symlink_to(target_file)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks not supported on this platform")
        collector = FileCollector()
        collected = collector.collect(self.test_path)
        self.assertIn(target_file, collected)
        self.assertIn(symlink, collected)

    def test_collect_recursive_deeper_than_max_depth(self):
        # Create nested directories deeper than max_depth
        current_dir = self.test_path
        for i in range(5):
            current_dir = current_dir / f"dir{i}"
            current_dir.mkdir()
            (current_dir / f"file{i}.txt").write_text(f"content{i}")
        collector = FileCollector()
        collected = collector.collect_recursive(self.test_path, max_depth=3)

        # Directories deeper than depth 3 should not be included
        current_dir = self.test_path
        for i in range(3):
            current_dir = current_dir / f"dir{i}"
            self.assertIn(current_dir, collected)
        for i in range(3,5):
            current_dir = current_dir / f"dir{i}"
            self.assertNotIn(current_dir, collected)

        # Files in directory 3 are in depth 4
        current_dir = self.test_path
        for i in range(2):
            current_dir = current_dir / f"dir{i}"
            self.assertIn(current_dir / f"file{i}.txt", collected)
        for i in range(2,5):
            current_dir = current_dir / f"dir{i}"
            self.assertNotIn(current_dir / f"file{i}.txt", collected)

    def test_collect_files_with_unusual_names(self):
        filenames = [
            "file with spaces.txt",
            "unicodé_файл.txt",
            "special_!@#$%^&*().txt",
            "1234567890.txt"
        ]
        for name in filenames:
            (self.test_path / name).write_text("content")
        collector = FileCollector()
        collected = collector.collect(self.test_path)
        for name in filenames:
            self.assertIn(self.test_path / name, collected)

    def test_collect_with_nonexistent_rules_file(self):
        file1 = self.test_path / "file1.txt"
        file1.write_text("content1")
        rules_file = self.test_path / "nonexistent_rules.yaml"
        collector = FileCollector()
        collected = collector.collect(self.test_path, rules_file_path=rules_file)
        self.assertIn(file1, collected)

    def test_collect_with_file_path_instead_of_directory(self):
        file1 = self.test_path / "file1.txt"
        file1.write_text("content1")
        collector = FileCollector()
        with self.assertRaises(NotADirectoryError):
            collector.collect(file1)

    def test_collect_nonexistent_path(self):
        collector = FileCollector()
        nonexistent_path = self.test_path / "does_not_exist"
        with self.assertRaises(FileNotFoundError):
            collector.collect(nonexistent_path)

if __name__ == "__main__":
    unittest.main(failfast=True)