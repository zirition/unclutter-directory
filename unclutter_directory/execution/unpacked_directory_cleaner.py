"""
Unpacked Directory Cleaner - Handles cleaning of unpacked directories after archive processing.
"""

from pathlib import Path

from ..commons import get_logger
from ..comparison import ArchiveDirectoryComparator
from ..config.organize_config import OrganizeConfig
from .delete_strategy import create_delete_strategy

logger = get_logger()


class UnpackedDirectoryCleaner:
    """Orchestrates the comparison and deletion of unpacked directories that are identical to archives."""

    def __init__(self, config: OrganizeConfig):
        """
        Initialize the UnpackedDirectoryCleaner.

        Args:
            config: Configuration object containing deletion and dry-run settings.
        """
        self.config = config
        self.comparator = ArchiveDirectoryComparator(
            include_hidden=config.include_hidden
        )
        self.delete_strategy = create_delete_strategy(
            always_delete=config.always_delete,
            never_delete=config.never_delete,
            interactive=not (
                config.dry_run or config.always_delete or config.never_delete
            ),
        )

    def clean(self, original_archive_path: Path, final_archive_path: Path) -> None:
        """
        Clean the unpacked directory if it is identical to the final archive.

        Args:
            original_archive_path: The original path of the archive (used to locate the unpacked dir).
            final_archive_path: The final path of the archive after processing.
        """
        logger.info(
            f"Checking for unpacked directory to clean for archive: {final_archive_path}"
        )
        expected_dir_path = original_archive_path.parent / original_archive_path.stem

        if not expected_dir_path.exists():
            logger.debug(f"Unpacked directory not found: {expected_dir_path}")
            return

        if not expected_dir_path.is_dir():
            logger.warning(
                f"Expected path exists but is not a directory: {expected_dir_path}"
            )
            return

        logger.info(
            f"Comparing archive {final_archive_path} with directory {expected_dir_path}"
        )
        result = self.comparator.compare_archive_and_directory(
            final_archive_path, expected_dir_path
        )

        if not result.identical:
            logger.info(
                f"Archive and directory are not identical. Differences: {result.differences}"
            )
            return

        logger.info(
            "Archive and directory are identical. Checking deletion strategy..."
        )
        if self.delete_strategy.should_delete_directory(
            expected_dir_path, final_archive_path
        ):
            logger.info(f"Proceeding with deletion of {expected_dir_path}")
            self.delete_strategy.perform_deletion(
                expected_dir_path, final_archive_path, dry_run=self.config.dry_run
            )
        else:
            logger.info(f"Deletion skipped for {expected_dir_path}")
