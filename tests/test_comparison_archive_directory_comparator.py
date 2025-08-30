"""
Tests for ArchiveDirectoryComparator.
"""

import tempfile
import unittest
import zipfile
from pathlib import Path

import py7zr

from unclutter_directory.comparison import ArchiveDirectoryComparator, ComparisonResult


class TestArchiveDirectoryComparator(unittest.TestCase):
    """Test ArchiveDirectoryComparator functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.comparator = ArchiveDirectoryComparator()

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_no_duplicates_found(self):
        """Test when no archive-directory pairs exist."""
        # Create empty directory
        result = self.comparator.find_potential_duplicates(self.root)
        self.assertEqual(len(result), 0)

    def test_zip_without_matching_directory(self):
        """Test ZIP file without corresponding directory."""
        # Create a zip file
        zip_path = self.root / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file1.txt", "content")

        result = self.comparator.find_potential_duplicates(self.root)
        self.assertEqual(len(result), 0)  # No corresponding directory

    def test_zip_with_matching_directory(self):
        """Test ZIP file with corresponding directory."""
        # Create directory
        test_dir = self.root / "test"
        test_dir.mkdir()

        # Create zip file
        zip_path = self.root / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file1.txt", "content")

        result = self.comparator.find_potential_duplicates(self.root)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], zip_path)
        self.assertEqual(result[0][1], test_dir)

    def test_7z_with_matching_directory(self):
        """Test 7Z file with corresponding directory."""
        # Create directory
        test_dir = self.root / "test"
        test_dir.mkdir()

        # Create 7z file
        seven_zip_path = self.root / "test.7z"
        with py7zr.SevenZipFile(seven_zip_path, "w") as szf:
            szf.writestr("file1.txt", "content")

        result = self.comparator.find_potential_duplicates(self.root)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], seven_zip_path)
        self.assertEqual(result[0][1], test_dir)

    def test_compare_identical_structures(self):
        """Test comparison of identical structures."""
        # Create directory with files
        test_dir = self.root / "test"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.txt").write_text("content2")

        # Create identical zip file
        zip_path = self.root / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(test_dir / "file1.txt", "file1.txt")
            zf.write(test_dir / "file2.txt", "file2.txt")

        result = self.comparator.compare_archive_and_directory(zip_path, test_dir)
        self.assertTrue(result.identical)
        self.assertEqual(len(result.differences), 0)

    def test_compare_different_structures(self):
        """Test comparison of different structures."""
        # Create directory
        test_dir = self.root / "test"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("content1")

        # Create different zip file
        zip_path = self.root / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file2.txt", "different content")

        result = self.comparator.compare_archive_and_directory(zip_path, test_dir)
        self.assertFalse(result.identical)
        self.assertGreater(len(result.differences), 0)

    def test_unsupported_archive_format(self):
        """Test handling of unsupported archive format."""
        # Create directory
        test_dir = self.root / "test"
        test_dir.mkdir()

        # Create file with unsupported extension
        unsupported_path = self.root / "test.tar.gz"
        unsupported_path.write_text("fake archive")

        result = self.comparator.compare_archive_and_directory(
            unsupported_path, test_dir
        )
        self.assertFalse(result.identical)
        self.assertIn("Unsupported archive format", result.differences[0])

    def test_compare_summary(self):
        """Test comparison summary generation."""
        # Create two comparison results
        result1 = ComparisonResult(
            self.root / "test1.zip", self.root / "test1", True, [], [], []
        )
        result2 = ComparisonResult(
            self.root / "test2.zip", self.root / "test2", False, [], [], ["difference"]
        )

        summary = self.comparator.get_comparison_summary([result1, result2])
        self.assertEqual(summary["total_comparisons"], 2)
        self.assertEqual(summary["identical"], 1)
        self.assertEqual(summary["different"], 1)
        self.assertEqual(summary["identical_percentage"], 50.0)


if __name__ == "__main__":
    unittest.main()
