import unittest
import zipfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory

from unclutter_directory.entities.file import File
from unclutter_directory.entities.compressed_archive import ZipArchive


class TestFileClass(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_file_properties(self):
        """Test file property calculations"""
        test_file = self.root / "test.txt"
        test_file.write_text("Test content")

        file_obj = File.from_path(test_file)
        self.assertEqual(file_obj.size, 12)
        self.assertFalse(file_obj.is_directory)
        self.assertEqual(file_obj.name, "test.txt")
        self.assertEqual(file_obj.path, self.root)

    def test_directory_size_calculation(self):
        """Test directory size aggregation"""
        # Create directory structure
        (self.root / "dir").mkdir()
        (self.root / "dir/file1.txt").write_text("Content")
        (self.root / "dir/subdir").mkdir()
        (self.root / "dir/subdir/file2.txt").write_text("Longer content")

        dir_obj = File.from_path(self.root / "dir")
        expected_size = 8 + 13  # Sizes of both files
        self.assertEqual(dir_obj.size, expected_size)
        self.assertTrue(dir_obj.is_directory)

    def test_empty_directory_properties(self):
        """Test handling of empty directories"""
        empty_dir = self.root / "empty"
        empty_dir.mkdir()

        dir_obj = File.from_path(empty_dir)
        self.assertEqual(dir_obj.size, 0)
        self.assertEqual(dir_obj.date, 0)
        self.assertTrue(dir_obj.is_directory)

    def test_directory_date_calculation(self):
        """Test directory uses newest file modification date"""
        test_dir = self.root / "dated"
        test_dir.mkdir()

        old_file = test_dir / "old.txt"
        old_file.touch()
        old_time = datetime.now() - timedelta(days=10)
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))

        new_file = test_dir / "new.txt"
        new_file.touch()

        dir_obj = File.from_path(test_dir)
        self.assertEqual(dir_obj.date, new_file.stat().st_mtime)


class TestZipArchiveHandler(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.create_test_zip()

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_test_zip(self):
        """Create test zip with various entry types"""
        self.zip_path = self.root / "test.zip"
        with zipfile.ZipFile(self.zip_path, "w") as zf:
            # Add regular file
            zf.writestr("file.txt", "Content")

            # Add empty directory
            zf.writestr("empty_dir/", "")

            # Add nested structure
            zf.writestr("nested/file.txt", "Nested content")

            # Add zero-byte file
            zf.writestr("zero.txt", "")

    def test_zip_file_extraction(self):
        """Test reading valid zip file contents"""
        zip_file = File.from_path(self.zip_path)
        archive = ZipArchive()
        files = archive.get_files(zip_file)

        self.assertEqual(len(files), 4)

        # Verify directory entry
        dir_entry = next(f for f in files if f.name == "empty_dir/")
        self.assertEqual(dir_entry.size, 0)

        # Verify nested file
        nested_file = next(f for f in files if f.name == "nested/file.txt")
        self.assertEqual(nested_file.size, 14)

    def test_corrupted_zip_handling(self):
        """Test error handling for invalid zip files"""
        corrupt_zip = self.root / "corrupt.zip"
        corrupt_zip.write_bytes(b"invalid data")

        archive = ZipArchive()
        with self.assertLogs(level="ERROR") as cm:
            files = archive.get_files(File.from_path(corrupt_zip))
            self.assertEqual(len(files), 0)
            self.assertIn("Error reading zip file", cm.output[0])


class TestRarArchiveHandler(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.create_test_rar()

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_test_rar(self):
        """Create test RAR file (simulated due to Python limitations)"""
        self.rar_path = self.root / "test.rar"
        # In real usage, create actual RAR file using external tools
        self.rar_path.touch()


class TestEdgeCases(unittest.TestCase):
    def test_special_characters_in_archives(self):
        """Test handling of special characters in archive entries"""
        with TemporaryDirectory() as td:
            zip_path = Path(td) / "special.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("fißéñâme.txt", "Special content")
                zf.writestr("space name.txt", "Content")

            archive = ZipArchive()
            files = archive.get_files(File.from_path(zip_path))
            self.assertEqual(len(files), 2)
            self.assertIn("fißéñâme.txt", [f.name for f in files])

    def test_large_directory_size(self):
        """Test handling of directories with many files"""
        with TemporaryDirectory() as td:
            test_dir = Path(td) / "large"
            test_dir.mkdir()

            # Create 1000 files
            for i in range(1000):
                (test_dir / f"file_{i}.txt").touch()

            dir_obj = File.from_path(test_dir)
            self.assertEqual(dir_obj.size, 0)  # All files are empty
            self.assertTrue(dir_obj.is_directory)


if __name__ == "__main__":
    unittest.main(failfast=True)
