import tempfile
import zipfile
from pathlib import Path

from unclutter_directory.comparison.archive_directory_comparator import (
    ArchiveDirectoryComparator,
)


def test_delete_unpacked_with_unicode_filenames():
    """Test delete-unpacked command with unicode filenames that have combining characters."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a directory with proper unicode
        dir_path = temp_path / "Imágenes"  # Proper unicode with precomposed á
        dir_path.mkdir()

        # Create some test files
        (dir_path / "test1.txt").write_text("content1")
        (dir_path / "test2.txt").write_text("content2")

        # Create ZIP with the same content but with combining characters in the directory name
        # This simulates the actual issue we're facing
        archive_path = temp_path / "Imágenes.zip"
        with zipfile.ZipFile(archive_path, "w") as z:
            # Using combining character (U+0301) instead of precomposed accented character (U+00E1)
            # Also add the directory entry to simulate the real case
            z.writestr("Ima\u0301genes/", "")  # Directory entry
            z.writestr("Ima\u0301genes/test1.txt", "content1")
            z.writestr("Ima\u0301genes/test2.txt", "content2")

        # Test the comparator directly
        comparator = ArchiveDirectoryComparator()
        result = comparator.compare_archive_and_directory(archive_path, dir_path)

        # After the fix with unicode normalization, this should be identical
        assert result.identical, (
            f"Files should be identical but found differences: {result.differences}"
        )


def test_unicode_normalization_fix():
    """Test that we can normalize unicode strings to handle combining characters."""
    import unicodedata

    # Strings with combining characters vs precomposed characters
    combining = "Ima\u0301genes"  # I + combining acute accent
    precomposed = "Imágenes"  # Proper á character

    # They look the same but are different
    assert combining != precomposed

    # Normalize them to the same form
    normalized_combining = unicodedata.normalize("NFC", combining)
    normalized_precomposed = unicodedata.normalize("NFC", precomposed)

    # Now they should be equal
    assert normalized_combining == normalized_precomposed


def test_unicode_normalization_in_comparator():
    """Test that the comparator normalizes unicode strings correctly."""
    from unclutter_directory.comparison.archive_directory_comparator import (
        ArchiveDirectoryComparator,
    )

    comparator = ArchiveDirectoryComparator()

    # Test the normalization method
    combining = "Ima\u0301genes"
    precomposed = "Imágenes"

    normalized_combining = comparator._normalize_unicode(combining)
    normalized_precomposed = comparator._normalize_unicode(precomposed)

    # They should be equal after normalization
    assert normalized_combining == normalized_precomposed


def test_delete_unpacked_with_real_case():
    """Test with a real case that simulates the actual issue reported."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create directory with combining characters (as it appears in the filesystem)
        dir_path = temp_path / "Ima\u0301genes"  # Using combining character
        dir_path.mkdir()

        # Create some test files
        (dir_path / "test1.txt").write_text("content1")
        (dir_path / "test2.txt").write_text("content2")

        # Create ZIP with precomposed characters (as it might appear in some ZIP files)
        archive_path = temp_path / "Ima\u0301genes.zip"
        with zipfile.ZipFile(archive_path, "w") as z:
            # Using precomposed character in ZIP
            z.writestr("Imágenes/", "")  # Directory entry with precomposed character
            z.writestr("Imágenes/test1.txt", "content1")
            z.writestr("Imágenes/test2.txt", "content2")

        # Test the comparator directly
        comparator = ArchiveDirectoryComparator()
        result = comparator.compare_archive_and_directory(archive_path, dir_path)

        # After the fix, this should be identical despite the unicode differences
        assert result.identical, (
            f"Files should be identical but found differences: {result.differences}"
        )
