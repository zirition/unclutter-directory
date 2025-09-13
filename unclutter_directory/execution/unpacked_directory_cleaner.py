"""
Unpacked Directory Cleaner - Handles cleaning of unpacked directories after archive processing.
"""

import shutil
from pathlib import Path

from ..commons import get_logger
from ..comparison import ArchiveDirectoryComparator
from ..config.organize_config import OrganizeConfig

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

        # Create confirmation handler locally to avoid circular imports
        from ..factories.component_factory import ComponentFactory

        confirmation_handler = ComponentFactory.create_confirmation_handler(self.config)

        # Use confirmation handler to decide whether to delete
        context_info = f"directory '{expected_dir_path.name}' (identical to '{final_archive_path.name}')"
        prompt_template = (
            "Delete duplicate directory '{context}'? [Y(es)/N(o)/A(ll)/Never]: "
        )
        cache_key = str(expected_dir_path.parent)

        if confirmation_handler.should_execute(
            context_info=context_info,
            prompt_template=prompt_template,
            cache_key=cache_key,
            action_type="delete",
        ):
            logger.info(f"Proceeding with deletion of {expected_dir_path}")
            if self.config.never_delete:
                logger.info(f"[DRY RUN] Would delete directory: {expected_dir_path}")
            else:
                shutil.rmtree(expected_dir_path)
                logger.info(f"✅ Deleted duplicate directory: {expected_dir_path}")
        else:
            logger.info(f"Deletion skipped for {expected_dir_path}")
