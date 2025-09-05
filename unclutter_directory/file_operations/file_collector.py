from pathlib import Path
from typing import List, Optional

from ..commons import get_logger

logger = get_logger()


class FileCollector:
    """
    Responsible for collecting files from directories based on specified criteria.
    Handles filtering logic for hidden files and exclusions.
    """

    def __init__(self, include_hidden: bool = False):
        """
        Initialize file collector

        Args:
            include_hidden: Whether to include hidden files (starting with '.')
        """
        self.include_hidden = include_hidden

    def collect(
        self, target_dir: Path, rules_file_path: Optional[Path] = None
    ) -> List[Path]:
        """
        Collect files from target directory

        Args:
            target_dir: Directory to collect files from
            rules_file_path: Rules file to exclude from collection

        Returns:
            List of file paths that should be processed
        """
        try:
            # Get all items in directory
            all_items = list(target_dir.iterdir())
        except PermissionError as e:
            logger.error(f"Permission denied accessing directory: {target_dir}")
            raise e
        except Exception as e:
            logger.error(f"Error accessing directory {target_dir}: {e}")
            raise e

        # Apply filters
        filtered_items = []

        for item in all_items:
            # Filter hidden files if not included
            if not self.include_hidden and item.name.startswith("."):
                logger.debug(f"Skipping hidden item: {item}")
                continue

            # Filter out rules file if it's in the same directory
            if (
                rules_file_path
                and rules_file_path.parent == target_dir
                and item == rules_file_path
            ):
                logger.debug(f"Skipping rules file: {item}")
                continue

            filtered_items.append(item)

        logger.debug(f"Collected {len(filtered_items)} items from {target_dir}")
        return filtered_items

    def collect_recursive(
        self,
        target_dir: Path,
        max_depth: int = 1,
        rules_file_path: Optional[Path] = None,
    ) -> List[Path]:
        """
        Collect files recursively up to specified depth

        Args:
            target_dir: Directory to collect files from
            max_depth: Maximum recursion depth (1 = no recursion)
            rules_file_path: Rules file to exclude from collection

        Returns:
            List of file paths that should be processed
        """
        if max_depth < 1:
            return []

        collected_files = []

        # Collect files from current directory
        current_files = self.collect(target_dir, rules_file_path)
        collected_files.extend(current_files)

        # Recurse into subdirectories if depth allows
        if max_depth > 1:
            for item in current_files:
                if item.is_dir():
                    sub_files = self.collect_recursive(
                        item, max_depth - 1, rules_file_path
                    )
                    collected_files.extend(sub_files)

        return collected_files
