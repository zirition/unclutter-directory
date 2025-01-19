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
            case_sensitive = rule.get("case_sensitive", False)
            if self._file_matches_conditions(file, rule.get("conditions", {}), case_sensitive):
                return rule

            # If the check_archive condition is set, check the contents of the archive it the rule apply
            if rule.get("check_archive", {}) and archive_manager is not None:
                for archived_file in archive_manager.get_files(file):
                    if self._file_matches_conditions(
                        archived_file, rule.get("conditions", {}), case_sensitive
                    ):
                        return rule
        return None

    def _get_archive_manager(self, file: File) -> CompressedArchive:
        if file.name.endswith(".zip"):
            return ZipArchive()
        return None

    def _file_matches_conditions(self, file: File, conditions: Dict, case_sensitive: bool) -> bool:
        name = file.name


        if "start" in conditions:
            if case_sensitive:
                if not name.startswith(conditions["start"]):
                    return False
            else:
                if not name.lower().startswith(conditions["start"].lower()):
                    return False
        if "end" in conditions:
            if case_sensitive:
                if not name.endswith(conditions["end"]):
                    return False
            else:
                if not name.lower().endswith(conditions["end"].lower()):
                    return False

        if "contain" in conditions:
            if case_sensitive:
                if conditions["contain"] not in name:
                    return False
            else:
                if conditions["contain"].lower() not in name.lower():
                    return False
        if "regex" in conditions:
            import re

            if case_sensitive:
                if not re.match(conditions["regex"], name):
                    return False
            else:
                # Use a case-insensitive regex pattern
                if not re.match(conditions["regex"], name, re.IGNORECASE):
                    return False

        # Size conditions
        size = file.size
        if "larger" in conditions and size <= parse_size(conditions["larger"]):
            return False
        if "smaller" in conditions and size >= parse_size(conditions["smaller"]):
            return False

        # Age conditions
        age_seconds = file.date
        if "older" in conditions and age_seconds < parse_time(conditions["older"]):
            return False
        if "newer" in conditions and age_seconds > parse_time(conditions["newer"]):
            return False

        return True
