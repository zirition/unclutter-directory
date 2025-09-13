"""Action execution module for unclutter_directory.

This module provides the ActionExecutor class responsible for executing various file organization actions
such as moving files, deleting files/directories, and compressing files to ZIP archives.
It handles conflict resolution and path management for robust file operations.

Supported action types:
- 'move': Relocate files to specified target directories while preserving relative paths
- 'delete': Remove files or directories permanently
- 'compress': Archive files/directories into ZIP files with optional removal of originals

The module uses conflict resolution to avoid overwriting existing files and provides
comprehensive error handling for all file operations.
"""

from pathlib import Path

from unclutter_directory.commons import get_logger, validations

from ..commons.aliases import Rule
from ..config.organize_config import OrganizeConfig
from ..entities.compressed_archive import get_archive_manager
from ..entities.file import File
from .action_strategy_factory import ActionStrategyFactory
from .unpacked_directory_cleaner import UnpackedDirectoryCleaner

logger = get_logger()


class ActionExecutor:
    """Executes file organization actions based on configuration using Strategy pattern.

    The ActionExecutor class encapsulates the logic for performing different types of actions
    on files and directories. It now uses the Strategy pattern for better maintainability,
    testability, and extensibility.

    The action configuration dictionary should contain:
    - type: One of 'move', 'delete', or 'compress'
    - target: Required for 'move' and 'compress', specifies destination path

    Attributes:
        action (Dict): Configuration dictionary defining the action to be performed
        strategy_factory (ActionStrategyFactory): Factory for creating action strategies
    """

    def __init__(
        self, action: dict, strategy_factory: ActionStrategyFactory | None = None
    ):
        """Initialize ActionExecutor with action configuration.

        Args:
            action (Dict): Action configuration dictionary containing:
                - type: The action type ('move', 'delete', or 'compress')
                - target: Optional target path for move/compress actions (absolute or relative)
            strategy_factory (ActionStrategyFactory, optional): Factory for creating strategies.
                Uses default factory if not provided.

        Example:
            >>> executor = ActionExecutor({'type': 'move', 'target': 'sorted'})
            >>> executor = ActionExecutor({'type': 'delete'})
        """
        self.action = action
        self.strategy_factory = strategy_factory or ActionStrategyFactory()

    @property
    def supported_actions(self) -> list[str]:
        """Get list of supported action types.

        Returns:
            List of supported action type strings
        """
        return self.strategy_factory.get_available_actions()

    def execute_action(
        self, file_path: Path, parent_path: Path, rule: Rule, config: OrganizeConfig
    ) -> Path | None:
        """Execute the configured action on a file with validation and error handling.
        Main entry point for performing file organization actions. Uses Strategy pattern
        to delegate execution to appropriate strategy based on action type.
        Args:
            file_path (Path): Path of the file or directory to process
            parent_path (Path): Base directory path for target resolution and relative calculations
            rule (Rule): The rule that matched this file
            config (OrganizeConfig): Configuration for the organize command
        Supported Actions:
            - move: Requires 'target' parameter, moves file to specified location
            - delete: No additional parameters required, removes file/directory
            - compress: Requires 'target' parameter, archives file/directory to ZIP
        Note:
            Invalid action types or validation failures are logged as warnings
            and the action is skipped without raising exceptions.
        Returns:
            Optional[Path]: The final path after action execution, or None if action failed or was skipped
        """
        action_type = self.action.get("type")
        target = self.action.get("target", "")

        # Validate action structure using centralized VALID_ACTIONS
        if not action_type or action_type not in validations.VALID_ACTIONS:
            logger.warning(f"Invalid action type for file {file_path}")
            return None
        if action_type in ["move", "compress"] and not target:
            logger.warning(f"Missing target for {action_type} action on {file_path}")
            return None

        # Create strategy instance
        strategy = self.strategy_factory.create_strategy(action_type, logger)
        if not strategy:
            logger.warning(
                f"Unsupported action type '{action_type}' for file {file_path}"
            )
            return None

        # Pre-execute cleanup check
        should_clean = rule.get("delete_unpacked_on_match", False)
        manager = get_archive_manager(File.from_path(file_path))
        is_preexisting_archive = not file_path.is_dir() and manager is not None

        # Execute action using strategy
        try:
            final_path = strategy.execute(file_path, parent_path, target)
            if should_clean and is_preexisting_archive and final_path is not None:
                try:
                    logger.info(
                        f"Cleaning unpacked directory for preexisting archive {file_path}"
                    )
                    cleaner = UnpackedDirectoryCleaner(config)
                    cleaner.clean(file_path, final_path)
                except Exception as clean_e:
                    logger.error(
                        f"Error during unpacked directory cleanup for {file_path}: {clean_e}"
                    )
            return final_path
        except Exception as e:
            logger.error(f"❌ Unexpected error processing {file_path}: {e}")
            return None
