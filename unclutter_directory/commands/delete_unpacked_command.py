"""
Delete Unpacked Command - Removes uncompressed directories that match compressed files.
"""

import shutil

from ..commons import get_logger, setup_logging
from ..comparison import ArchiveDirectoryComparator, ComparisonResult
from ..config.delete_unpacked_config import DeleteUnpackedConfig
from ..execution.confirmation import ConfirmationHandler
from ..factories.component_factory import ComponentFactory

logger = get_logger()


class DeleteUnpackedCommand:
    """Command for checking and removing duplicate directories that match compressed files."""

    def __init__(self, config: DeleteUnpackedConfig):
        """
        Initialize delete-unpacked command.

        Args:
            config: Configuration for the delete-unpacked operation
        """
        self.config = config
        self.comparator = ArchiveDirectoryComparator(
            include_hidden=config.include_hidden
        )
        self.confirmation_handler: ConfirmationHandler = (
            ComponentFactory.create_confirmation_handler(config)
        )

    def execute(self) -> None:
        """
        Execute the check duplicates operation.
        Finds archive-directory pairs and compares them, potentially deleting duplicates.
        """
        try:
            setup_logging(self.config.quiet)
            logger.info(
                f"🔍 Scanning for uncompressed directories in {self.config.target_dir}"
            )

            # Find potential archive-directory pairs
            potential_pairs = self.comparator.find_potential_duplicates(
                self.config.target_dir
            )

            if not potential_pairs:
                logger.info("✅ No potential archive-directory duplicates found")
                return

            logger.info(
                f"📦 Found {len(potential_pairs)} potential duplicates to check"
            )

            # Compare each pair
            all_results = []
            deleted_count = 0

            for archive_path, directory_path in potential_pairs:
                logger.info(f"Comparing: {archive_path.name} ↔ {directory_path.name}")

                try:
                    # Compare archive and directory
                    result = self.comparator.compare_archive_and_directory(
                        archive_path, directory_path
                    )

                    if result.identical:
                        logger.info("✅ Structures are identical")

                        # Ask user if should delete the directory using confirmation handler
                        context_info = f"directory '{directory_path.name}' (identical to '{archive_path.name}')"
                        prompt_template = "Delete duplicate directory '{context}'? [Y(es)/N(o)/A(ll)/Never]: "
                        cache_key = str(directory_path.parent)

                        if self.confirmation_handler.should_execute(
                            context_info=context_info,
                            prompt_template=prompt_template,
                            cache_key=cache_key,
                            action_type="delete",
                        ):
                            # Perform the deletion directly
                            shutil.rmtree(directory_path)
                            deleted_count += 1
                        else:
                            logger.info(
                                f"⏭️  Skipping deletion of {directory_path.name}"
                            )
                    else:
                        logger.info("❌ Structures differ:")
                        for diff in result.differences[:5]:  # Show first 5 differences
                            logger.info(f"   • {diff}")
                        if len(result.differences) > 5:
                            logger.info(
                                f"   • ... and {len(result.differences) - 5} more differences"
                            )

                    all_results.append(result)

                except Exception as e:
                    logger.error(
                        f"❌ Error comparing {archive_path.name} with {directory_path.name}: {e}"
                    )
                    continue

            # Print summary
            self._print_summary(all_results, deleted_count, len(potential_pairs))

        except KeyboardInterrupt:
            logger.info("\n⏹️  Operation cancelled by user")
        except Exception as e:
            logger.error(f"❌ Unexpected error during check-duplicates operation: {e}")
            raise

    def _print_summary(
        self, results: list[ComparisonResult], deleted_count: int, total_pairs: int
    ) -> None:
        """Print a summary of the operation."""
        summary = self.comparator.get_comparison_summary(results)

        logger.info("\n📊 Summary:")
        logger.info(f"   • Total pairs checked: {total_pairs}")
        logger.info(
            f"   • Identical structures: {summary['identical']} ({summary['identical_percentage']:.1f}%)"
        )
        logger.info(f"   • Different structures: {summary['different']}")
        logger.info(f"   • Directories deleted: {deleted_count}")
