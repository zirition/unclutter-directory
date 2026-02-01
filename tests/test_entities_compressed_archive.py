"""
Tests for CompressedArchive implementations and handlers.
"""

import tempfile
import gzip
import tarfile
from pathlib import Path

import pytest

from unclutter_directory.entities.compressed_archive import (
    ArchiveHandlerChain,
    GzipArchive,
    GzipHandler,
    TarGzArchive,
    TarGzHandler,
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
        "gz": File(data_dir, "test.gz", None, None),
        "tar_gz": File(data_dir, "test.tar.gz", None, None),
        "tgz": File(data_dir, "test.tgz", None, None),
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


def test_gzip_archive_get_files(temp_dir):
    """Test GzipArchive get_files method for single-file archives."""
    archive_path = temp_dir / "sample.iso.gz"
    content = b"hello world"
    with gzip.open(archive_path, "wb") as gz:
        gz.write(content)

    file_obj = File(temp_dir, archive_path.name, None, None)
    archive = GzipArchive()
    files = archive.get_files(file_obj)

    assert len(files) == 1
    assert files[0].name == "sample.iso"
    assert files[0].size == len(content)


def test_tar_gz_archive_get_files(temp_dir):
    """Test TarGzArchive get_files method for multi-file archives."""
    archive_path = temp_dir / "sample.tar.gz"
    file1 = temp_dir / "file1.txt"
    file2 = temp_dir / "subdir" / "file2.txt"
    file2.parent.mkdir()
    file1.write_text("hello")
    file2.write_text("world")

    with tarfile.open(archive_path, "w:gz") as tarf:
        tarf.add(file1, arcname="file1.txt")
        tarf.add(file2, arcname="subdir/file2.txt")

    file_obj = File(temp_dir, archive_path.name, None, None)
    archive = TarGzArchive()
    files = archive.get_files(file_obj)

    names = {f.name for f in files}
    assert "file1.txt" in names
    assert "subdir/file2.txt" in names


@pytest.mark.parametrize(
    "handler_class, expected_zip, expected_rar, expected_7z, expected_gz, expected_tar_gz, expected_tgz",
    [
        (ZipHandler, True, False, False, False, False, False),
        (RarHandler, False, True, False, False, False, False),
        (SevenZipHandler, False, False, True, False, False, False),
        (GzipHandler, False, False, False, True, False, False),
        (TarGzHandler, False, False, False, False, True, True),
    ],
    ids=[
        "zip_handler",
        "rar_handler",
        "seven_zip_handler",
        "gzip_handler",
        "tar_gz_handler",
    ],
)
def test_handler_can_handle(
    sample_files,
    handler_class,
    expected_zip,
    expected_rar,
    expected_7z,
    expected_gz,
    expected_tar_gz,
    expected_tgz,
):
    """Test handler can_handle method for different archive types."""
    handler = handler_class()
    assert handler.can_handle(sample_files["zip"]) == expected_zip
    assert handler.can_handle(sample_files["rar"]) == expected_rar
    assert handler.can_handle(sample_files["7z"]) == expected_7z
    assert handler.can_handle(sample_files["gz"]) == expected_gz
    assert handler.can_handle(sample_files["tar_gz"]) == expected_tar_gz
    assert handler.can_handle(sample_files["tgz"]) == expected_tgz


@pytest.mark.parametrize(
    "file_key, expected_type",
    [
        ("zip", ZipArchive),
        ("7z", SevenZipArchive),
        ("gz", GzipArchive),
        ("tar_gz", TarGzArchive),
        ("unsupported", None),
    ],
    ids=["zip", "7z", "gz", "tar_gz", "unsupported"],
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
        ("gz", GzipArchive),
        ("tar_gz", TarGzArchive),
        ("tgz", TarGzArchive),
    ],
    ids=["zip", "7z", "rar", "gz", "tar_gz", "tgz"],
)
def test_get_archive_manager(sample_files, file_key, expected_type):
    """Test get_archive_manager for different archive types."""
    file_obj = sample_files[file_key]
    archive = get_archive_manager(file_obj)
    assert isinstance(archive, expected_type)
