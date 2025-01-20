import zipfile

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List

from unclutter_directory import commons

logger = commons.get_logger()


class File:
    def __init__(self, path: Path, name: str, date, size: int):
        self.path = path
        self.name = name
        if isinstance(date, tuple):
            date = datetime(*date).timestamp()
        self.date = date
        self.size = size

    @staticmethod
    def from_path(file_path: Path):
        path = file_path.parent
        name = file_path.name
        date = file_path.stat().st_mtime
        size = file_path.stat().st_size
        return File(Path(path), name, date, size)

class CompressedArchive(ABC):
    @abstractmethod
    def compress(self, file: File):
        pass

    def get_files(self, file: File) -> List[File]:
        pass


class ZipArchive(CompressedArchive):
    def __init__(self):
        pass

    def compress(self, file: File):
        archive_path = file.path / f"{file.name}.zip"
        with zipfile.ZipFile(archive_path, "a") as zipf:
            zipf.write(file.name)

    def get_files(self, file: File) -> List[File]:
        archive_path = file.path / file.name
        try:
            with zipfile.ZipFile(archive_path, "r") as zipf:
                return [
                    File(
                        file.path,
                        name,
                        zipf.getinfo(name).date_time,
                        zipf.getinfo(name).file_size,
                    )
                    for name in zipf.namelist()
                ]
        except zipfile.BadZipFile:
            logger.error(f"❌ Error reading zip file: {archive_path}")
            return []
