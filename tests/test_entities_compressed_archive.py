import bz2
import gzip
import lzma
import tarfile
import tempfile
from pathlib import Path

import pytest

from unclutter_directory.entities.compressed_archive import (
    ArchiveHandlerChain,
    Bzip2Archive,
    Bzip2Handler,
    GzipArchive,
    GzipHandler,
    RarArchive,
    RarHandler,
    SevenZipArchive,
    SevenZipHandler,
    TarBz2Archive,
    TarBz2Handler,
    TarGzArchive,
    TarGzHandler,
    TarXzArchive,
    TarXzHandler,
    XzArchive,
    XzHandler,
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
        "tar_bz2": File(data_dir, "test.tar.bz2", None, None),
        "tbz2": File(data_dir, "test.tbz2", None, None),
        "tbz": File(data_dir, "test.tbz", None, None),
        "tar_xz": File(data_dir, "test.tar.xz", None, None),
        "txz": File(data_dir, "test.txz", None, None),
        "bz2": File(data_dir, "test.bz2", None, None),
        "bz": File(data_dir, "test.bz", None, None),
        "xz": File(data_dir, "test.xz", None, None),
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


def test_bzip2_archive_get_files(temp_dir):
    """Test Bzip2Archive get_files method for single-file archives."""
    archive_path = temp_dir / "sample.iso.bz2"
    content = b"hello world"
    with bz2.BZ2File(archive_path, "wb") as bz:
        bz.write(content)

    file_obj = File(temp_dir, archive_path.name, None, None)
    archive = Bzip2Archive()
    files = archive.get_files(file_obj)

    assert len(files) == 1
    assert files[0].name == "sample.iso"
    assert files[0].size == len(content)


def test_xz_archive_get_files(temp_dir):
    """Test XzArchive get_files method for single-file archives."""
    archive_path = temp_dir / "sample.iso.xz"
    content = b"hello world"
    with lzma.open(archive_path, "wb") as xz:
        xz.write(content)

    file_obj = File(temp_dir, archive_path.name, None, None)
    archive = XzArchive()
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


def test_tar_bz2_archive_get_files(temp_dir):
    """Test TarBz2Archive get_files method for multi-file archives."""
    archive_path = temp_dir / "sample.tar.bz2"
    file1 = temp_dir / "file1.txt"
    file2 = temp_dir / "subdir" / "file2.txt"
    file2.parent.mkdir()
    file1.write_text("hello")
    file2.write_text("world")

    with tarfile.open(archive_path, "w:bz2") as tarf:
        tarf.add(file1, arcname="file1.txt")
        tarf.add(file2, arcname="subdir/file2.txt")

    file_obj = File(temp_dir, archive_path.name, None, None)
    archive = TarBz2Archive()
    files = archive.get_files(file_obj)

    names = {f.name for f in files}
    assert "file1.txt" in names
    assert "subdir/file2.txt" in names


def test_tar_xz_archive_get_files(temp_dir):
    """Test TarXzArchive get_files method for multi-file archives."""
    archive_path = temp_dir / "sample.tar.xz"
    file1 = temp_dir / "file1.txt"
    file2 = temp_dir / "subdir" / "file2.txt"
    file2.parent.mkdir()
    file1.write_text("hello")
    file2.write_text("world")

    with tarfile.open(archive_path, "w:xz") as tarf:
        tarf.add(file1, arcname="file1.txt")
        tarf.add(file2, arcname="subdir/file2.txt")

    file_obj = File(temp_dir, archive_path.name, None, None)
    archive = TarXzArchive()
    files = archive.get_files(file_obj)

    names = {f.name for f in files}
    assert "file1.txt" in names
    assert "subdir/file2.txt" in names


@pytest.mark.parametrize(
    "handler_class, expected_zip, expected_rar, expected_7z, expected_gz, expected_tar_gz, expected_tgz, expected_tar_bz2, expected_tbz2, expected_tbz, expected_tar_xz, expected_txz, expected_bz2, expected_bz, expected_xz",
    [
        (ZipHandler, True, False, False, False, False, False, False, False, False, False, False, False, False, False),
        (RarHandler, False, True, False, False, False, False, False, False, False, False, False, False, False, False),
        (SevenZipHandler, False, False, True, False, False, False, False, False, False, False, False, False, False, False),
        (GzipHandler, False, False, False, True, False, False, False, False, False, False, False, False, False, False),
        (TarGzHandler, False, False, False, False, True, True, False, False, False, False, False, False, False, False),
        (TarBz2Handler, False, False, False, False, False, False, True, True, True, False, False, False, False, False),
        (TarXzHandler, False, False, False, False, False, False, False, False, False, True, True, False, False, False),
        (Bzip2Handler, False, False, False, False, False, False, False, False, False, False, False, True, True, False),
        (XzHandler, False, False, False, False, False, False, False, False, False, False, False, False, False, True),
    ],
    ids=[
        "zip_handler",
        "rar_handler",
        "seven_zip_handler",
        "gzip_handler",
        "tar_gz_handler",
        "tar_bz2_handler",
        "tar_xz_handler",
        "bzip2_handler",
        "xz_handler",
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
    expected_tar_bz2,
    expected_tbz2,
    expected_tbz,
    expected_tar_xz,
    expected_txz,
    expected_bz2,
    expected_bz,
    expected_xz,
):
    """Test handler can_handle method for different archive types."""
    handler = handler_class()
    assert handler.can_handle(sample_files["zip"]) == expected_zip
    assert handler.can_handle(sample_files["rar"]) == expected_rar
    assert handler.can_handle(sample_files["7z"]) == expected_7z
    assert handler.can_handle(sample_files["gz"]) == expected_gz
    assert handler.can_handle(sample_files["tar_gz"]) == expected_tar_gz
    assert handler.can_handle(sample_files["tgz"]) == expected_tgz
    assert handler.can_handle(sample_files["tar_bz2"]) == expected_tar_bz2
    assert handler.can_handle(sample_files["tbz2"]) == expected_tbz2
    assert handler.can_handle(sample_files["tbz"]) == expected_tbz
    assert handler.can_handle(sample_files["tar_xz"]) == expected_tar_xz
    assert handler.can_handle(sample_files["txz"]) == expected_txz
    assert handler.can_handle(sample_files["bz2"]) == expected_bz2
    assert handler.can_handle(sample_files["bz"]) == expected_bz
    assert handler.can_handle(sample_files["xz"]) == expected_xz


@pytest.mark.parametrize(
    "file_key, expected_type",
    [
        ("zip", ZipArchive),
        ("7z", SevenZipArchive),
        ("gz", GzipArchive),
        ("tar_gz", TarGzArchive),
        ("tar_bz2", TarBz2Archive),
        ("tar_xz", TarXzArchive),
        ("bz2", Bzip2Archive),
        ("xz", XzArchive),
        ("unsupported", None),
    ],
    ids=["zip", "7z", "gz", "tar_gz", "tar_bz2", "tar_xz", "bz2", "xz", "unsupported"],
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
        ("tar_bz2", TarBz2Archive),
        ("tbz2", TarBz2Archive),
        ("tbz", TarBz2Archive),
        ("tar_xz", TarXzArchive),
        ("txz", TarXzArchive),
        ("bz2", Bzip2Archive),
        ("bz", Bzip2Archive),
        ("xz", XzArchive),
    ],
    ids=["zip", "7z", "rar", "gz", "tar_gz", "tgz", "tar_bz2", "tbz2", "tbz", "tar_xz", "txz", "bz2", "bz", "xz"],
)
def test_get_archive_manager(sample_files, file_key, expected_type):
    """Test get_archive_manager for different archive types."""
    file_obj = sample_files[file_key]
    archive = get_archive_manager(file_obj)
    assert isinstance(archive, expected_type)
