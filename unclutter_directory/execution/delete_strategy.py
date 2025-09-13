"""
Utility functions for the check-duplicates command.
"""

from pathlib import Path

from ..commons import get_logger

logger = get_logger()


def perform_deletion(
    directory_path: Path, archive_path: Path, dry_run: bool = False
) -> bool:
    """
    Perform the actual directory deletion or log the action in dry-run mode.

    Args:
        directory_path: Path to directory to delete
        archive_path: Path to corresponding archive
        dry_run: If True, only log what would be deleted

    Returns:
        True if deletion was successful or would be successful (dry run), False otherwise
    """
    if dry_run:
        logger.info(f"[DRY RUN] Would delete directory: {directory_path}")
        return True

    try:
        import shutil

        shutil.rmtree(directory_path)
        logger.info(f"✅ Deleted duplicate directory: {directory_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to delete directory {directory_path}: {e}")
        return False
