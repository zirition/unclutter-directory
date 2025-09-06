import os
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from unclutter_directory.entities.compressed_archive import ZipArchive
from unclutter_directory.entities.file import File


@pytest.fixture
def temp_dir():
    """Fixture común para directorio temporal."""
    with TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def create_zip_file(temp_dir):
    """Fixture para crear un zip con contenido variado."""

    def _create_zip(contents):
        zip_path = temp_dir / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for name, data in contents.items():
                if name.endswith("/"):
                    zf.writestr(name, "")
                else:
                    zf.writestr(name, data)
        return zip_path

    return _create_zip


@pytest.mark.parametrize(
    "path_type, expected_size, expected_is_dir",
    [
        ("file", 12, False),  # Archivo con contenido
        ("empty_dir", 0, True),  # Directorio vacío
    ],
)
def test_file_properties(temp_dir, path_type, expected_size, expected_is_dir):
    """Test parametrizado para propiedades básicas de archivos y directorios."""
    root = temp_dir
    if path_type == "file":
        test_path = root / "test.txt"
        test_path.write_text("Test content")
    else:  # empty_dir
        test_path = root / "empty"
        test_path.mkdir()

    file_obj = File.from_path(test_path)
    assert file_obj.size == expected_size
    assert file_obj.is_directory == expected_is_dir
    if not expected_is_dir:
        assert file_obj.name == "test.txt"


def test_directory_size_calculation(temp_dir):
    """Test cálculo de tamaño de directorio con archivos."""
    root = temp_dir
    dir_path = root / "dir"
    dir_path.mkdir()
    (dir_path / "file1.txt").write_text("Content")  # size 7
    subdir = dir_path / "subdir"
    subdir.mkdir()
    (subdir / "file2.txt").write_text("Longer content")  # size 14

    dir_obj = File.from_path(dir_path)
    assert dir_obj.size == 21  # 7 + 14
    assert dir_obj.is_directory


def test_directory_date_calculation(temp_dir):
    """Test fecha de directorio usa la más nueva."""
    root = temp_dir
    test_dir = root / "dated"
    test_dir.mkdir()

    old_file = test_dir / "old.txt"
    old_file.touch()
    old_time = datetime.now() - timedelta(days=10)
    os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))

    new_file = test_dir / "new.txt"
    new_file.touch()

    dir_obj = File.from_path(test_dir)
    assert dir_obj.date == new_file.stat().st_mtime


@pytest.mark.parametrize(
    "entries, expected_files",
    [
        (
            {
                "file.txt": "Content",
                "empty_dir/": "",
                "nested/file.txt": "Nested content",
                "zero.txt": "",
            },
            {
                "file.txt": 7,
                "empty_dir/": 0,
                "nested/file.txt": 14,
                "zero.txt": 0,
            },
        ),
    ],
)
def test_zip_file_extraction(create_zip_file, entries, expected_files):
    """Test parametrizado para extracción de zip con diferentes entradas."""
    zip_path = create_zip_file(entries)
    zip_file = File.from_path(zip_path)
    archive = ZipArchive()
    files = archive.get_files(zip_file)

    assert len(files) == len(expected_files)
    for f in files:
        assert f.size == expected_files[f.name]


def test_corrupted_zip_handling(caplog, temp_dir):
    """Test manejo de zip corrupto."""
    root = temp_dir
    corrupt_zip = root / "corrupt.zip"
    corrupt_zip.write_bytes(b"invalid data")

    archive = ZipArchive()
    files = archive.get_files(File.from_path(corrupt_zip))
    assert len(files) == 0
    assert "Error reading zip file" in caplog.text


@pytest.mark.parametrize(
    "special_names",
    [
        ["fißéñâme.txt", "space name.txt"],
    ],
)
def test_special_characters_in_archives(temp_dir, special_names, create_zip_file):
    """Test parametrizado para caracteres especiales en archives."""
    contents = dict.fromkeys(special_names, "Content")
    zip_path = create_zip_file(contents)
    archive = ZipArchive()
    files = archive.get_files(File.from_path(zip_path))
    assert len(files) == len(special_names)
    assert all(name in [f.name for f in files] for name in special_names)


def test_large_directory_size(temp_dir):
    """Test directorio con muchos archivos."""
    test_dir = temp_dir / "large"
    test_dir.mkdir()

    for i in range(1000):
        (test_dir / f"file_{i}.txt").touch()

    dir_obj = File.from_path(test_dir)
    assert dir_obj.size == 0  # Todos vacíos
    assert dir_obj.is_directory
