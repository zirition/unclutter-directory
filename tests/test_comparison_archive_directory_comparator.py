"""
Tests for ArchiveDirectoryComparator.
"""

import tempfile
import zipfile
from pathlib import Path

import pytest

from unclutter_directory.comparison import ArchiveDirectoryComparator, ComparisonResult


@pytest.fixture
def comparator_and_root():
    """Set up test fixtures."""
    temp_dir = tempfile.TemporaryDirectory()
    root = Path(temp_dir.name)
    comparator = ArchiveDirectoryComparator()
    yield comparator, root
    temp_dir.cleanup()


def test_no_duplicates_found(comparator_and_root):
    """Test when no archive-directory pairs exist."""
    comparator, root = comparator_and_root
    # Create empty directory
    result = comparator.find_potential_duplicates(root)
    assert len(result) == 0


@pytest.mark.parametrize("extension", [".zip", ".7z"])
def test_without_matching_directory(comparator_and_root, extension, request):
    """Test archive file without corresponding directory."""
    comparator, root = comparator_and_root
    # Create archive file
    if extension == ".zip":
        with zipfile.ZipFile(root / f"test{extension}", "w") as zf:
            zf.writestr("file1.txt", "content")
    else:  # .7z
        import py7zr

        with py7zr.SevenZipFile(root / f"test{extension}", "w") as szf:
            szf.writestr("file1.txt", "content")

    result = comparator.find_potential_duplicates(root)
    assert len(result) == 0  # No corresponding directory


@pytest.mark.parametrize("extension", [".zip", ".7z"])
def test_with_matching_directory(comparator_and_root, extension, request):
    """Test archive file with corresponding directory."""
    comparator, root = comparator_and_root
    # Create directory
    test_dir = root / "test"
    test_dir.mkdir()

    # Create archive file
    archive_path = root / f"test{extension}"
    if extension == ".zip":
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("file1.txt", "content")
    else:  # .7z
        import py7zr

        with py7zr.SevenZipFile(archive_path, "w") as szf:
            szf.writestr("file1.txt", "content")

    result = comparator.find_potential_duplicates(root)
    assert len(result) == 1
    assert result[0][0] == archive_path
    assert result[0][1] == test_dir


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(
            {
                "identical": True,
                "files": [("file1.txt", "content1"), ("file2.txt", "content2")],
            },
            id="identical",
        ),
        pytest.param(
            {
                "identical": False,
                "files": [("file1.txt", "content1")],
                "zip_files": [("file2.txt", "different content")],
            },
            id="different",
        ),
    ],
)
def test_compare_structures(comparator_and_root, case):
    """Test comparison of structures."""
    comparator, root = comparator_and_root
    # Create directory with files
    test_dir = root / "test"
    test_dir.mkdir()
    for filename, content in case.get("files", []):
        (test_dir / filename).write_text(content)

    # Create zip file
    zip_path = root / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for filename, content in case.get("files", []):
            zf.writestr(filename, content)
        for filename, content in case.get("zip_files", []):
            zf.writestr(filename, content)

    result = comparator.compare_archive_and_directory(zip_path, test_dir)
    assert result.identical == case["identical"]
    if case["identical"]:
        assert len(result.differences) == 0
    else:
        assert len(result.differences) > 0


def test_unsupported_archive_format(comparator_and_root):
    """Test handling of unsupported archive format."""
    comparator, root = comparator_and_root
    # Create directory
    test_dir = root / "test"
    test_dir.mkdir()

    # Create file with unsupported extension
    unsupported_path = root / "test.tar.gz"
    unsupported_path.write_text("fake archive")

    result = comparator.compare_archive_and_directory(unsupported_path, test_dir)
    assert not result.identical
    assert "Unsupported archive format" in result.differences[0]


def test_compare_summary(comparator_and_root):
    """Test comparison summary generation."""
    comparator, root = comparator_and_root
    # Create two comparison results
    result1 = ComparisonResult(root / "test1.zip", root / "test1", True, [], [], [])
    result2 = ComparisonResult(
        root / "test2.zip", root / "test2", False, [], [], ["difference"]
    )

    summary = comparator.get_comparison_summary([result1, result2])
    assert summary["total_comparisons"] == 2
    assert summary["identical"] == 1
    assert summary["different"] == 1
    assert summary["identical_percentage"] == 50.0
