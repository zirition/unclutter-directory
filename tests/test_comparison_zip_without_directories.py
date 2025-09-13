"""
Tests for ArchiveDirectoryComparator with ZIP files that don't contain directory entries.
"""

import tempfile
import zipfile
from pathlib import Path

from unclutter_directory.comparison import ArchiveDirectoryComparator


def test_zip_without_directory_entries():
    """Test ZIP archive without directory entries matches directory structure correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a directory structure
        test_dir = temp_path / "test_dir"
        test_dir.mkdir()

        # Create subdirectories with files
        subdir1 = test_dir / "subdir1"
        subdir1.mkdir()
        subdir2 = test_dir / "subdir2"
        subdir2.mkdir()

        # Create files
        (test_dir / "file1.txt").write_text("content1")
        (subdir1 / "file2.txt").write_text("content2")
        (subdir2 / "file3.txt").write_text("content3")

        # Create a ZIP file without directory entries
        zip_path = temp_path / "test_without_dirs.zip"
        with zipfile.ZipFile(zip_path, "w") as zipf:
            # Only add files, not directory entries
            zipf.write(test_dir / "file1.txt", "file1.txt")
            zipf.write(subdir1 / "file2.txt", "subdir1/file2.txt")
            zipf.write(subdir2 / "file3.txt", "subdir2/file3.txt")

        # Verify the ZIP doesn't contain directory entries
        with zipfile.ZipFile(zip_path, "r") as zipf:
            namelist = zipf.namelist()
            # Should not contain directory entries
            assert "subdir1/" not in namelist
            assert "subdir2/" not in namelist
            # Should contain only file entries
            assert set(namelist) == {
                "file1.txt",
                "subdir1/file2.txt",
                "subdir2/file3.txt",
            }

        # Compare structures - should be identical
        comparator = ArchiveDirectoryComparator()
        result = comparator.compare_archive_and_directory(zip_path, test_dir)

        # Should be identical
        assert result.identical, (
            f"Structures should be identical but have differences: {result.differences}"
        )
        assert len(result.differences) == 0


def test_zip_with_directory_entries():
    """Test ZIP archive with directory entries matches directory structure correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a directory structure
        test_dir = temp_path / "test_dir"
        test_dir.mkdir()

        # Create subdirectories with files
        subdir1 = test_dir / "subdir1"
        subdir1.mkdir()
        subdir2 = test_dir / "subdir2"
        subdir2.mkdir()

        # Create files
        (test_dir / "file1.txt").write_text("content1")
        (subdir1 / "file2.txt").write_text("content2")
        (subdir2 / "file3.txt").write_text("content3")

        # Create a ZIP file with directory entries
        zip_path = temp_path / "test_with_dirs.zip"
        with zipfile.ZipFile(zip_path, "w") as zipf:
            # Add directory entries explicitly
            zipf.writestr("subdir1/", "")
            zipf.writestr("subdir2/", "")
            # Add files
            zipf.write(test_dir / "file1.txt", "file1.txt")
            zipf.write(subdir1 / "file2.txt", "subdir1/file2.txt")
            zipf.write(subdir2 / "file3.txt", "subdir2/file3.txt")

        # Verify the ZIP contains directory entries
        with zipfile.ZipFile(zip_path, "r") as zipf:
            namelist = zipf.namelist()
            # Should contain directory entries
            assert "subdir1/" in namelist
            assert "subdir2/" in namelist

        # Compare structures - should be identical
        comparator = ArchiveDirectoryComparator()
        result = comparator.compare_archive_and_directory(zip_path, test_dir)

        # Should be identical
        assert result.identical, (
            f"Structures should be identical but have differences: {result.differences}"
        )
        assert len(result.differences) == 0
