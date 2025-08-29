from typing import List, Dict

from ..entities.file import File
from ..entities.compressed_archive import CompressedArchive, get_archive_manager

from ..commons.validations import parse_size, parse_time


"""
FileMatcher provides functionality to match files against a set of predefined rules.

The class supports various matching conditions including filename patterns, size constraints,
age constraints, and archive content inspection for compressed files.
"""

class FileMatcher:
    def __init__(self, rules: List[Dict]):
        """
        Initialize FileMatcher with a list of matching rules.

        Args:
            rules (List[Dict]): A list of dictionaries, where each dictionary
                represents a rule with keys like 'conditions', 'case_sensitive',
                'is_directory', and 'check_archive'.
        """
        self.rules = rules

    def match(self, file: File) -> Dict:
        """
        Match a file against the configured rules.

        Checks the file against each rule in order. Rules can include conditions
        for filename patterns (start, end, contain, regex), size (larger, smaller),
        age (older, newer), and archive content inspection.

        Args:
            file (File): The file object to match against the rules.

        Returns:
            Dict: The first matching rule dictionary, or None if no rules match.
        """
        archive_manager = self._get_archive_manager(file)

        for rule in self.rules:
            case_sensitive = rule.get("case_sensitive", False)
            is_directory_rule = rule.get("is_directory", False)

            if file.is_directory != is_directory_rule:
                continue

            if self._file_matches_conditions(
                file, rule.get("conditions", {}), case_sensitive
            ):
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
        """
        Get the appropriate archive manager for compressed files.

        Uses Chain of Responsibility pattern to determine the correct archive manager
        based on the file extension. Currently supports ZIP and RAR archive formats.

        Args:
            file (File): The file to get an archive manager for.

        Returns:
            CompressedArchive or None: An archive manager instance if the file
            is a supported compressed format, None otherwise.
        """
        return get_archive_manager(file)

    def _file_matches_conditions(
        self, file: File, conditions: Dict, case_sensitive: bool
    ) -> bool:
        """
        Check if a file matches the specified conditions.

        Supports multiple condition types: filename prefix/suffix matching,
        substring containment, regex matching, size comparisons, and age comparisons.

        Args:
            file (File): The file object to check.
            conditions (Dict): Dictionary of conditions to match against.
            case_sensitive (bool): Whether to perform case-sensitive matching.

        Returns:
            bool: True if all conditions are met, False otherwise.
        """
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
