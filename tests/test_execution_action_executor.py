import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from typing import List
from unittest.mock import patch

from unclutter_directory.execution.action_executor import ActionExecutor


class TestActionExecutor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test_file.txt"
        self.test_file.touch()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _create_test_structure(self, structure: List[str]):
        for item in structure:
            path = self.temp_dir / item
            if path.suffix:  # is file
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            else:  # is directory
                path.mkdir(parents=True)

    def test_move_basic(self):
        """Move file to an empty directory"""
        target = self.temp_dir / "target"
        action = {"type": "move", "target": str(target)}

        ActionExecutor(action).execute_action(self.test_file, self.temp_dir)

        moved_file = target / self.test_file.name
        self.assertTrue(moved_file.exists())
        self.assertFalse(self.test_file.exists())

    def test_move_with_conflict(self):
        """Move file with existing file in target"""
        target = self.temp_dir / "target"
        target.mkdir()
        (target / self.test_file.name).touch()  # Existing file

        action = {"type": "move", "target": str(target)}
        ActionExecutor(action).execute_action(self.test_file, self.temp_dir)

        moved_file = target / "test_file_1.txt"
        self.assertTrue(moved_file.exists())
        self.assertFalse(self.test_file.exists())

    def test_move_absolute_path(self):
        """Move using absolute path"""
        target = self.temp_dir / "absolute_target"
        action = {"type": "move", "target": str(target.resolve())}

        ActionExecutor(action).execute_action(self.test_file, self.temp_dir)

        self.assertTrue((target / self.test_file.name).exists())

    def test_move_nested_directories(self):
        """Move to nonexistant nested directories"""
        target = self.temp_dir / "nested/target/directory"
        action = {"type": "move", "target": str(target)}

        ActionExecutor(action).execute_action(self.test_file, self.temp_dir)

        self.assertTrue((target / self.test_file.name).exists())

    def test_delete_basic(self):
        """Basic delete"""
        action = {"type": "delete"}

        ActionExecutor(action).execute_action(self.test_file, self.temp_dir)

        self.assertFalse(self.test_file.exists())

    def test_compress_basic(self):
        """Basic compression without conflicts"""
        target = self.temp_dir / "compressed"
        action = {"type": "compress", "target": str(target)}

        ActionExecutor(action).execute_action(self.test_file, self.temp_dir)

        zip_file = target / "test_file.zip"
        self.assertTrue(zip_file.exists())
        self.assertFalse(self.test_file.exists())  # Original must be deleted

    def test_compress_with_conflict(self):
        """Compress file with colliding file name"""
        target = self.temp_dir / "compressed"
        target.mkdir()
        (target / "test_file.zip").touch()  # Existing file

        action = {"type": "compress", "target": str(target)}
        ActionExecutor(action).execute_action(self.test_file, self.temp_dir)

        self.assertTrue((target / "test_file_1.zip").exists())

    def test_compress_content_validation(self):
        """Test zip content"""
        target = self.temp_dir / "compressed"
        content = "Test content"
        self.test_file.write_text(content)

        ActionExecutor({"type": "compress", "target": str(target)}).execute_action(
            self.test_file, self.temp_dir
        )

        with zipfile.ZipFile(target / "test_file.zip") as z:
            with z.open(self.test_file.name) as f:
                self.assertEqual(f.read().decode(), content)

    def test_compress_forbidden_extensions(self):
        """Don't compress already compressed files"""
        forbidden_files = [
            self.temp_dir / "test.zip",
            self.temp_dir / "test.rar",
            self.temp_dir / "test.7z",
        ]

        for file in forbidden_files:
            file.touch()
            with self.subTest(file=file), self.assertLogs(level="INFO") as logs:
                ActionExecutor(
                    {"type": "compress", "target": str(self.temp_dir)}
                ).execute_action(file, self.temp_dir)
                self.assertIn("Skipping compression for archive file", logs.output[0])
                self.assertFalse((self.temp_dir / (file.name + ".zip")).exists())

    def test_compress_non_existent_directory(self):
        """Compress to non existent directory"""
        target = self.temp_dir / "non/existent/directory"
        action = {"type": "compress", "target": str(target)}

        ActionExecutor(action).execute_action(self.test_file, self.temp_dir)

        self.assertTrue((target / "test_file.zip").exists())

    def test_invalid_action(self):
        """Handle malformed or unrecognized actions"""
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

        for action, expected_msg in zip(test_cases, expected_log_messages):
            with self.subTest(action=action), self.assertLogs(level="WARNING") as logs:
                ActionExecutor(action).execute_action(self.test_file, self.temp_dir)
                self.assertTrue(
                    any(expected_msg in log for log in logs.output),
                    f"Expected message '{expected_msg}' not found in logs",
                )

    @patch("shutil.move")
    def test_move_error_handling(self, mock_move):
        """Error handling during movement"""
        mock_move.side_effect = Exception("Simulated error")
        action = {"type": "move", "target": str(self.temp_dir / "target")}

        with self.assertLogs(level="ERROR") as logs:
            ActionExecutor(action).execute_action(self.test_file, self.temp_dir)
            self.assertIn("Unexpected error processing", logs.output[0])

    def test_delete_error_handling(self):
        """Error handling during delete"""
        with patch.object(Path, "unlink") as mock_unlink, self.assertLogs(
            level="ERROR"
        ) as logs:
            mock_unlink.side_effect = Exception("Simulated error")
            ActionExecutor({"type": "delete"}).execute_action(
                self.test_file, self.temp_dir
            )
            self.assertIn("Error deleting ", logs.output[0])

    def test_delete_directory(self):
        """Delete directory with nested content"""
        test_dir = self.temp_dir / "test_dir"
        self._create_test_structure(["test_dir/file1.txt", "test_dir/subdir/file2.txt"])

        ActionExecutor({"type": "delete"}).execute_action(test_dir, self.temp_dir)
        self.assertFalse(test_dir.exists())

    def test_compress_directory(self):
        """Compress directory with nested structure"""
        test_dir = self.temp_dir / "to_compress"
        self._create_test_structure(
            ["to_compress/file.txt", "to_compress/subdir/nested.txt"]
        )

        ActionExecutor({"type": "compress", "target": "archives"}).execute_action(
            test_dir, self.temp_dir
        )

        zip_path = self.temp_dir / "archives" / "to_compress.zip"
        with zipfile.ZipFile(zip_path) as z:
            self.assertIn("to_compress/file.txt", z.namelist())
            self.assertIn("to_compress/subdir/nested.txt", z.namelist())
        self.assertFalse(test_dir.exists())

    def test_compress_directory_conflict(self):
        """Handle directory compression naming conflicts"""
        target = self.temp_dir / "archives"
        target.mkdir()
        (target / "test_dir.zip").touch()

        test_dir = self.temp_dir / "test_dir"
        test_dir.mkdir()

        ActionExecutor({"type": "compress", "target": "archives"}).execute_action(
            test_dir, self.temp_dir
        )
        self.assertTrue((target / "test_dir_1.zip").exists())

    def test_move_directory(self):
        """Move directory with contents"""
        test_dir = self.temp_dir / "source"
        self._create_test_structure(["source/data.txt"])

        ActionExecutor({"type": "move", "target": "dest"}).execute_action(
            test_dir, self.temp_dir
        )

        moved = self.temp_dir / "dest" / "source"
        self.assertTrue(moved.exists())
        self.assertTrue((moved / "data.txt").exists())
        self.assertFalse(test_dir.exists())

    def test_compress_directory_with_archives(self):
        """Compress directory containing archive files"""
        test_dir = self.temp_dir / "mixed"
        self._create_test_structure(["mixed/data.zip", "mixed/backup.rar"])

        ActionExecutor({"type": "compress", "target": "output"}).execute_action(
            test_dir, self.temp_dir
        )

        with zipfile.ZipFile(self.temp_dir / "output" / "mixed.zip") as z:
            self.assertIn("mixed/data.zip", z.namelist())

    def test_directory_name_with_archive_extension(self):
        """Compress directory named like an archive file"""
        test_dir = self.temp_dir / "fake.zip"
        test_dir.mkdir()
        (test_dir / "file.txt").touch()

        ActionExecutor({"type": "compress", "target": "output"}).execute_action(
            test_dir, self.temp_dir
        )
        self.assertTrue((self.temp_dir / "output" / "fake.zip.zip").exists())

    def test_empty_directory_compression(self):
        """Compress empty directory"""
        test_dir = self.temp_dir / "empty"
        test_dir.mkdir()

        ActionExecutor({"type": "compress", "target": "archives"}).execute_action(
            test_dir, self.temp_dir
        )
        zip_path = self.temp_dir / "archives" / "empty.zip"
        self.assertTrue(zip_path.exists())

    def test_compress_directory_with_empty_subdirectory(self):
        """Compress directory containing an empty subdirectory"""
        test_dir = self.temp_dir / "dir"
        self._create_test_structure(
            [
                "dir/empty/",
            ]
        )

        ActionExecutor({"type": "compress", "target": "output"}).execute_action(
            test_dir, self.temp_dir
        )

        with zipfile.ZipFile(self.temp_dir / "output" / "dir.zip") as z:
            self.assertIn("dir/empty/", z.namelist())


if __name__ == "__main__":
    unittest.main(failfast=True)
