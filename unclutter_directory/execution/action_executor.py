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
from typing import Dict, List, Optional

from unclutter_directory.commons import validations

from .action_strategy_factory import ActionStrategyFactory

logger = validations.get_logger()


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
        self, action: Dict, strategy_factory: Optional[ActionStrategyFactory] = None
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
    def supported_actions(self) -> List[str]:
        """Get list of supported action types.

        Returns:
            List of supported action type strings
        """
        return self.strategy_factory.get_available_actions()

    def execute_action(self, file_path: Path, parent_path: Path) -> None:
        """Execute the configured action on a file with validation and error handling.

        Main entry point for performing file organization actions. Uses Strategy pattern
        to delegate execution to appropriate strategy based on action type.

        Args:
            file_path (Path): Path of the file or directory to process
            parent_path (Path): Base directory path for target resolution and relative calculations

        Supported Actions:
            - move: Requires 'target' parameter, moves file to specified location
            - delete: No additional parameters required, removes file/directory
            - compress: Requires 'target' parameter, archives file/directory to ZIP

        Note:
            Invalid action types or validation failures are logged as warnings
            and the action is skipped without raising exceptions.
        """
        action_type = self.action.get("type")
        target = self.action.get("target", "")

        # Validate action structure using centralized VALID_ACTIONS
        if not action_type or action_type not in validations.VALID_ACTIONS:
            logger.warning(f"Invalid action type for file {file_path}")
            return
        if action_type in ["move", "compress"] and not target:
            logger.warning(f"Missing target for {action_type} action on {file_path}")
            return

        # Create strategy instance
        strategy = self.strategy_factory.create_strategy(action_type, logger)
        if not strategy:
            logger.warning(
                f"Unsupported action type '{action_type}' for file {file_path}"
            )
            return

        # Execute action using strategy
        try:
            strategy.execute(file_path, parent_path, target)
        except Exception as e:
            logger.error(f"❌ Unexpected error processing {file_path}: {e}")
