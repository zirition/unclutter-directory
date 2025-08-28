import zipfile
import rarfile
from rarfile import RarFile

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List

from unclutter_directory.commons import validations

logger = validations.get_logger()


class File:
    def __init__(self, path: Path, name: str, date: float, size: int, is_directory: bool = False):
        self.path = path
        self.name = name
        if isinstance(date, tuple):
            date = self._validate_and_correct_date_tuple(date)
        self.date = date
        self.size = size
        self.is_directory = is_directory

    @staticmethod
    def _validate_and_correct_date_tuple(date_tuple):
        year = date_tuple[0]
        month = date_tuple[1] if len(date_tuple) > 1 else 1
        day = date_tuple[2] if len(date_tuple) > 2 else 1
        hour = date_tuple[3] if len(date_tuple) > 3 else 0
        minute = date_tuple[4] if len(date_tuple) > 4 else 0
        second = date_tuple[5] if len(date_tuple) > 5 else 0

        year = max(1, min(year, 9999))
        month = max(1, min(month, 12))
        day = max(1, min(day, 31))
        hour = max(0, min(hour, 23))
        minute = max(0, min(minute, 59))
        second = max(0, min(second, 59))

        try:
            return datetime(year, month, day, hour, minute, second).timestamp()
        except ValueError:
            return datetime(year, month, 28, hour, minute, second).timestamp()

    @staticmethod
    def from_path(file_path: Path):
        if file_path.is_dir():
            total_size = 0
            latest_mtime = 0
            for child in file_path.rglob('*'):
                if child.is_file():
                    total_size += child.stat().st_size
                    child_mtime = child.stat().st_mtime
                    latest_mtime = max(latest_mtime, child_mtime)
            return File(file_path.parent, file_path.name, latest_mtime, total_size, is_directory=True)
        else:
            stats = file_path.stat()
            return File(file_path.parent, file_path.name, stats.st_mtime, stats.st_size, is_directory=False)


class CompressedArchive(ABC):
    @abstractmethod
    def get_files(self, file: File) -> List[File]:
        pass


class ZipArchive(CompressedArchive):
    def __init__(self):
        pass

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

class RarArchive(CompressedArchive):
    def __init__(self):
        pass

    def get_files(self, file: File) -> List[File]:
        archive_path = file.path / file.name
        try:
            with RarFile(archive_path) as rarf:
                return [
                    File(
                        file.path,
                        name,
                        rarf.getinfo(name).date_time,
                        rarf.getinfo(name).file_size,
                    )
                    for name in rarf.namelist()
                ]
        except rarfile.Error:
            logger.error(f"❌ Error reading rar file: {archive_path}")
            return []

