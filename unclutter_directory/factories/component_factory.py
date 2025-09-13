import yaml

from unclutter_directory.commons.aliases import Rules

from ..commons import get_logger
from ..config.delete_unpacked_config import DeleteUnpackedConfig
from ..config.organize_config import ExecutionMode, OrganizeConfig
from ..execution.confirmation import (
    AutomaticConfirmationHandler,
    ConfirmationHandler,
    DryRunConfirmationHandler,
    InteractiveConfirmationHandler,
)
from ..file_operations.file_collector import FileCollector
from ..file_operations.file_matcher import FileMatcher

logger = get_logger()


class ComponentFactory:
    """
    Factory for creating configured components.
    Centralizes object creation and configuration logic.
    """

    @staticmethod
    def create_file_matcher(config: OrganizeConfig) -> FileMatcher:
        """
        Create configured FileMatcher with loaded rules

        Args:
            config: Configuration containing rules file path

        Returns:
            Configured FileMatcher instance

        Raises:
            RuntimeError: If rules cannot be loaded
        """
        rules = ComponentFactory._load_rules(config.rules_file)
        if rules is None:
            raise RuntimeError(f"Failed to load rules from {config.rules_file}")

        return FileMatcher(rules)

    @staticmethod
    def create_file_collector(config: OrganizeConfig) -> FileCollector:
        """
        Create configured FileCollector

        Args:
            config: Configuration containing collection preferences

        Returns:
            Configured FileCollector instance
        """
        return FileCollector(include_hidden=config.include_hidden)

    @staticmethod
    def create_confirmation_handler(config) -> ConfirmationHandler:
        """
        Create appropriate confirmation handler based on configuration.
        Works with both OrganizeConfig and DeleteUnpackedConfig.

        Args:
            config: Configuration determining handler type (OrganizeConfig or DeleteUnpackedConfig)

        Returns:
            Appropriate ConfirmationHandler instance
        """
        if config.execution_mode == ExecutionMode.DRY_RUN:
            return DryRunConfirmationHandler()
        elif config.execution_mode == ExecutionMode.AUTOMATIC:
            # For delete-unpacked, use always_delete flag. For organize, non-delete always True (handler internal logic).
            if isinstance(config, DeleteUnpackedConfig):
                return AutomaticConfirmationHandler(always_confirm=config.always_delete)
            else:  # OrganizeConfig
                # Non-delete actions always proceed in automatic mode (handler internal logic handles this)
                return AutomaticConfirmationHandler(always_confirm=True)
        elif config.execution_mode == ExecutionMode.INTERACTIVE:
            return InteractiveConfirmationHandler()
        else:
            # This should not happen with proper enum usage
            raise ValueError(f"Unknown execution mode: {config.execution_mode}")

    @staticmethod
    def _load_rules(rules_file: str) -> Rules:
        """
        Load rules from YAML file

        Args:
            rules_file: Path to rules file

        Returns:
            Loaded rules list or None if loading failed
        """
        try:
            with open(rules_file, encoding="utf-8") as f:
                rules = yaml.safe_load(f)

            if not isinstance(rules, list):
                logger.error(f"Rules file {rules_file} must contain a list")
                return None

            return rules

        except yaml.YAMLError as e:
            logger.error(f"YAML error in rules file {rules_file}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading rules file {rules_file}: {e}")
            return None
