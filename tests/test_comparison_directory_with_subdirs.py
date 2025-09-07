"""
Tests for DirectoryAnalyzer with subdirectories using real archive files.
"""

import tempfile
from pathlib import Path

import pytest

from unclutter_directory.comparison import ArchiveDirectoryComparator
from unclutter_directory.comparison.directory_analyzer import DirectoryAnalyzer


@pytest.fixture
def temp_dir():
    """Set up test fixtures."""
    with tempfile.TemporaryDirectory() as temp_name:
        root = Path(temp_name)
        yield root


def test_directory_analyzer_with_subdirectories(temp_dir):
    """Test DirectoryAnalyzer correctly includes subdirectory entries."""
    # Create directory structure with subdirectories
    test_dir = temp_dir / "test"
    test_dir.mkdir()

    # Create subdirectories
    subdir1 = test_dir / "subdir1"
    subdir1.mkdir()
    subdir2 = test_dir / "subdir2"
    subdir2.mkdir()

    # Create files in root and subdirectories
    (test_dir / "file1.txt").write_text("content1")
    (subdir1 / "file2.txt").write_text("content2")
    (subdir2 / "file3.txt").write_text("content3")

    # Analyze directory
    analyzer = DirectoryAnalyzer()
    files = analyzer.get_files(test_dir)

    # Convert to set of names for easier comparison
    file_names = {f.name for f in files}

    # Should include directory entries with trailing slashes
    expected_names = {
        "file1.txt",
        "subdir1/",
        "subdir1/file2.txt",
        "subdir2/",
        "subdir2/file3.txt",
    }

    assert file_names == expected_names
    # Verify directory entries have size 0
    for file in files:
        if file.name.endswith("/"):
            assert file.size == 0


def test_zip_with_subdirectories_real_file():
    """Test ZIP archive with subdirectories using real file."""
    data_dir = Path("tests/data/archives")
    zip_path = data_dir / "test_with_subdirs.zip"

    # Create corresponding directory structure
    test_dir = Path("tests/data/test_structure")

    # Compare structures
    comparator = ArchiveDirectoryComparator()
    result = comparator.compare_archive_and_directory(zip_path, test_dir)

    assert result.identical
    assert len(result.differences) == 0


def test_7z_with_subdirectories_real_file():
    """Test 7Z archive with subdirectories using real file."""
    data_dir = Path("tests/data/archives")
    archive_path = data_dir / "test_with_subdirs.7z"

    # Create corresponding directory structure
    test_dir = Path("tests/data/test_structure")

    # Compare structures
    comparator = ArchiveDirectoryComparator()
    result = comparator.compare_archive_and_directory(archive_path, test_dir)

    assert result.identical
    assert len(result.differences) == 0


def test_rar_with_subdirectories_real_file():
    """Test RAR archive with subdirectories using real file."""
    try:
        import rarfile  # noqa: F401
    except ImportError:
        pytest.skip("rarfile not available")

    data_dir = Path("tests/data/archives")
    archive_path = data_dir / "test_with_subdirs.rar"

    # Create corresponding directory structure
    test_dir = Path("tests/data/test_structure")

    # Compare structures
    comparator = ArchiveDirectoryComparator()
    result = comparator.compare_archive_and_directory(archive_path, test_dir)

    assert result.identical
    assert len(result.differences) == 0
