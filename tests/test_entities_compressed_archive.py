"""
Tests for CompressedArchive implementations and handlers.
"""

import tempfile
from pathlib import Path

import pytest

from unclutter_directory.entities.compressed_archive import (
    ArchiveHandlerChain,
    RarArchive,
    RarHandler,
    SevenZipArchive,
    SevenZipHandler,
    ZipArchive,
    ZipHandler,
    get_archive_manager,
)
from unclutter_directory.entities.file import File


@pytest.fixture
def temp_dir():
    """Set up test fixtures."""
    with tempfile.TemporaryDirectory() as temp_name:
        root = Path(temp_name)
        yield root


@pytest.fixture
def sample_files():
    """Fixture for sample File objects with different archive extensions."""
    data_dir = Path("tests/data/archives")
    return {
        "zip": File(data_dir, "test.zip", None, None),
        "rar": File(data_dir, "test.rar", None, None),
        "7z": File(data_dir, "test.7z", None, None),
    }


def test_zip_archive_get_files():
    """Test ZipArchive get_files method."""
    data_dir = Path("tests/data/archives")
    file_obj = File(data_dir, "test.zip", None, None)
    archive = ZipArchive()
    files = archive.get_files(file_obj)

    assert len(files) == 2
    assert files[0].name == "file1.txt"
    assert files[1].name == "file2.txt"


def test_rar_archive_get_files():
    """Test RarArchive get_files method."""
    data_dir = Path("tests/data/archives")
    file_obj = File(data_dir, "test.rar", None, None)
    archive = RarArchive()
    files = archive.get_files(file_obj)

    assert len(files) == 2
    assert files[0].name == "file1.txt"
    assert files[1].name == "file2.txt"


def test_seven_zip_archive_get_files():
    """Test SevenZipArchive get_files method."""
    data_dir = Path("tests/data/archives")
    file_obj = File(data_dir, "test.7z", None, None)
    archive = SevenZipArchive()
    files = archive.get_files(file_obj)

    assert len(files) == 2
    assert files[0].name == "file1.txt"
    assert files[1].name == "file2.txt"


@pytest.mark.parametrize(
    "handler_class, expected_zip, expected_rar, expected_7z",
    [
        (ZipHandler, True, False, False),
        (RarHandler, False, True, False),
        (SevenZipHandler, False, False, True),
    ],
    ids=["zip_handler", "rar_handler", "seven_zip_handler"],
)
def test_handler_can_handle(
    sample_files, handler_class, expected_zip, expected_rar, expected_7z
):
    """Test handler can_handle method for different archive types."""
    handler = handler_class()
    assert handler.can_handle(sample_files["zip"]) == expected_zip
    assert handler.can_handle(sample_files["rar"]) == expected_rar
    assert handler.can_handle(sample_files["7z"]) == expected_7z


@pytest.mark.parametrize(
    "file_key, expected_type",
    [
        ("zip", ZipArchive),
        ("7z", SevenZipArchive),
        ("unsupported", None),
    ],
    ids=["zip", "7z", "unsupported"],
)
def test_archive_handler_chain(sample_files, temp_dir, file_key, expected_type):
    """Test ArchiveHandlerChain get_archive_handler for different file types."""
    chain = ArchiveHandlerChain()
    if file_key == "unsupported":
        file_obj = File(temp_dir, "test.txt", None, None)
    else:
        file_obj = sample_files[file_key]
    archive = chain.get_archive_handler(file_obj)
    if expected_type is None:
        assert archive is None
    else:
        assert isinstance(archive, expected_type)


@pytest.mark.parametrize(
    "file_key, expected_type",
    [
        ("zip", ZipArchive),
        ("7z", SevenZipArchive),
        ("rar", RarArchive),
    ],
    ids=["zip", "7z", "rar"],
)
def test_get_archive_manager(sample_files, file_key, expected_type):
    """Test get_archive_manager for different archive types."""
    file_obj = sample_files[file_key]
    archive = get_archive_manager(file_obj)
    assert isinstance(archive, expected_type)
