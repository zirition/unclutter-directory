from typing import List, Dict

from .File import File, CompressedArchive, ZipArchive

from .commons import parse_size, parse_time

# Define core functions for library
class FileMatcher:
    def __init__(self, rules: List[Dict]):
        self.rules = rules

    def match(self, file: File) -> Dict:
        archive_manager = self._get_archive_manager(file)

        for rule in self.rules:
            if self._file_matches_conditions(file, rule.get("conditions", {})):
                return rule

            # If the check_archive condition is set, check the contents of the archive it the rule apply
            if rule.get("check_archive", {}) and archive_manager is not None:
                for archived_file in archive_manager.get_files(file):
                    if self._file_matches_conditions(archived_file, rule.get("conditions", {})):
                        return rule
        return None

    def _get_archive_manager(self, file: File) -> CompressedArchive:
        if file.name.endswith(".zip"):
            return ZipArchive()
        return None

    def _file_matches_conditions(self, file: File, conditions: Dict) -> bool:
        name = file.name

        # Name conditions
        if "start" in conditions and not name.startswith(conditions["start"]):
            return False
        if "end" in conditions and not name.endswith(conditions["end"]):
            return False
        if "contain" in conditions and conditions["contain"] not in name:
            return False
        if "regex" in conditions:
            import re

            if not re.match(conditions["regex"], name):
                return False

        # Size conditions
        size = file.size
        if "larger" in conditions and size <= parse_size(conditions["larger"]):
            return False
        if "smaller" in conditions and size >= parse_size(conditions["smaller"]):
            return False

        # Age conditions
        age_seconds = file.date
        if "older" in conditions and age_seconds < parse_time(
            conditions["older"]
        ):
            return False
        if "newer" in conditions and age_seconds > parse_time(
            conditions["newer"]
        ):
            return False

        return True

