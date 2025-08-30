"""
Tests for CompressedArchive implementations and handlers.
"""

import unittest
import tempfile
import zipfile
from pathlib import Path

from unclutter_directory.entities.compressed_archive import (
    ZipArchive,
    RarArchive,
    SevenZipArchive,
    ArchiveHandlerChain,
    ZipHandler,
    RarHandler,
    SevenZipHandler,
    get_archive_manager
)
from unclutter_directory.entities.file import File


class TestCompressedArchive(unittest.TestCase):
    """Test CompressedArchive base and implementations."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_zip_archive_get_files(self):
        """Test ZipArchive get_files method."""
        # Create a test zip file
        zip_path = self.root / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("file2.txt", "content2")

        file_obj = File(self.root, "test.zip", None, None)
        archive = ZipArchive()
        files = archive.get_files(file_obj)

        self.assertEqual(len(files), 2)
        self.assertEqual(files[0].name, "file1.txt")
        self.assertEqual(files[1].name, "file2.txt")

    def test_zip_handler_can_handle(self):
        """Test ZipHandler can_handle method."""
        zip_file = File(self.root, "test.zip", None, None)
        rar_file = File(self.root, "test.rar", None, None)
        seven_zip_file = File(self.root, "test.7z", None, None)

        handler = ZipHandler()
        self.assertTrue(handler.can_handle(zip_file))
        self.assertFalse(handler.can_handle(rar_file))
        self.assertFalse(handler.can_handle(seven_zip_file))

    def test_rar_handler_can_handle(self):
        """Test RarHandler can_handle method."""
        # Rar is harder to test without rarfile, so just check extension
        zip_file = File(self.root, "test.zip", None, None)
        rar_file = File(self.root, "test.rar", None, None)
        seven_zip_file = File(self.root, "test.7z", None, None)

        handler = RarHandler()
        self.assertFalse(handler.can_handle(zip_file))
        self.assertTrue(handler.can_handle(rar_file))
        self.assertFalse(handler.can_handle(seven_zip_file))

    def test_seven_zip_handler_can_handle(self):
        """Test SevenZipHandler can_handle method."""
        zip_file = File(self.root, "test.zip", None, None)
        rar_file = File(self.root, "test.rar", None, None)
        seven_zip_file = File(self.root, "test.7z", None, None)

        handler = SevenZipHandler()
        self.assertFalse(handler.can_handle(zip_file))
        self.assertFalse(handler.can_handle(rar_file))
        self.assertTrue(handler.can_handle(seven_zip_file))

    def test_archive_handler_chain_with_zip(self):
        """Test ArchiveHandlerChain with ZIP file."""
        chain = ArchiveHandlerChain()
        zip_file = File(self.root, "test.zip", None, None)
        archive = chain.get_archive_handler(zip_file)
        self.assertIsInstance(archive, ZipArchive)

    def test_archive_handler_chain_with_seven_zip(self):
        """Test ArchiveHandlerChain with 7Z file."""
        chain = ArchiveHandlerChain()
        seven_zip_file = File(self.root, "test.7z", None, None)
        archive = chain.get_archive_handler(seven_zip_file)
        self.assertIsInstance(archive, SevenZipArchive)

    def test_archive_handler_chain_with_unsupported(self):
        """Test ArchiveHandlerChain with unsupported file."""
        chain = ArchiveHandlerChain()
        unknown_file = File(self.root, "test.txt", None, None)
        archive = chain.get_archive_handler(unknown_file)
        self.assertIsNone(archive)

    def test_get_archive_manager_zip(self):
        """Test get_archive_manager with ZIP."""
        zip_file = File(self.root, "test.zip", None, None)
        archive = get_archive_manager(zip_file)
        self.assertIsInstance(archive, ZipArchive)

    def test_get_archive_manager_seven_zip(self):
        """Test get_archive_manager with 7z."""
        seven_zip_file = File(self.root, "test.7z", None, None)
        archive = get_archive_manager(seven_zip_file)
        self.assertIsInstance(archive, SevenZipArchive)

    def test_get_archive_manager_rar(self):
        """Test get_archive_manager with RAR."""
        rar_file = File(self.root, "test.rar", None, None)
        archive = get_archive_manager(rar_file)
        self.assertIsInstance(archive, RarArchive)


if __name__ == '__main__':
    unittest.main()