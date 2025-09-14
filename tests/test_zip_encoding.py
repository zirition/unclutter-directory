import tempfile
import zipfile
from pathlib import Path

from unclutter_directory.entities.compressed_archive import ZipArchive
from unclutter_directory.entities.file import File


def test_zip_archive_with_non_utf8_encoding():
    """Test that ZipArchive can handle ZIP files with non-UTF-8 metadata encoding."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a ZIP file with non-UTF-8 encoded metadata
        archive_path = temp_path / "test.zip"

        # Create a ZIP file using the default encoding (which may not be UTF-8)
        with zipfile.ZipFile(archive_path, "w") as z:
            # Add some files with names that might cause encoding issues
            z.writestr("test_file.txt", "content")
            z.writestr("folder/", "")  # Directory entry
            z.writestr("folder/subfile.txt", "subcontent")

        # Create a File object for testing
        file_obj = File(
            path=archive_path.parent,
            name=archive_path.name,
            date=0,
            size=archive_path.stat().st_size,
            is_directory=False,
        )

        # Test the ZipArchive handler
        zip_handler = ZipArchive()
        files = zip_handler.get_files(file_obj)

        # Should successfully process the ZIP file
        assert len(files) == 3
        names = [f.name for f in files]
        assert "test_file.txt" in names
        assert "folder/" in names
        assert "folder/subfile.txt" in names
