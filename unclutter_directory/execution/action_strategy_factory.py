"""Action Strategy Factory

This module provides the factory for creating action strategy instances.
It centralizes the creation logic and provides a clean interface for
strategy instantiation and management.

The factory pattern allows for:
- Centralized strategy management
- Easy addition of new strategies
- Strategy discovery and enumeration
- Consistent instance creation
"""

from typing import Dict, List, Optional, Type

from ..commons import validations
from .action_strategies import (
    ActionStrategy,
    CompressStrategy,
    DeleteStrategy,
    MoveStrategy,
)


class ActionStrategyFactory:
    """Factory for creating and managing action strategy instances.

    This factory provides a centralized way to create action strategies
    based on action types. It maintains a registry of available strategies
    and handles their instantiation with proper logging configuration.

    Attributes:
        _strategies: Dictionary mapping action types to strategy classes
    """

    _strategies: Dict[str, Type[ActionStrategy]] = {
        "move": MoveStrategy,
        "delete": DeleteStrategy,
        "compress": CompressStrategy,
    }

    @classmethod
    def create_strategy(
        cls, action_type: str, logger_instance=None
    ) -> Optional[ActionStrategy]:
        """Create a strategy instance for the specified action type.

        Args:
            action_type: Type of action ('move', 'delete', 'compress')
            logger_instance: Logger instance to pass to strategy.
                           Uses default logger if None

        Returns:
            ActionStrategy instance or None if action_type is not supported

        Example:
            >>> strategy = ActionStrategyFactory.create_strategy('move')
            >>> if strategy:
            ...     strategy.execute(file_path, parent_path, target)
        """
        if logger_instance is None:
            logger_instance = validations.get_logger()

        strategy_class = cls._strategies.get(action_type)
        if not strategy_class:
            return None

        return strategy_class(logger_instance)

    @classmethod
    def get_available_actions(cls) -> List[str]:
        """Get a list of all available action types.

        Returns:
            List of supported action type strings

        Example:
            >>> actions = ActionStrategyFactory.get_available_actions()
            >>> print(actions)  # ['move', 'delete', 'compress']
        """
        return list(cls._strategies.keys())

    @classmethod
    def is_action_supported(cls, action_type: str) -> bool:
        """Check if an action type is supported.

        Args:
            action_type: Action type to check

        Returns:
            True if action is supported, False otherwise

        Example:
            >>> ActionStrategyFactory.is_action_supported('move')  # True
            >>> ActionStrategyFactory.is_action_supported('custom')  # False
        """
        return action_type in cls._strategies

    @classmethod
    def register_strategy(
        cls, action_type: str, strategy_class: Type[ActionStrategy]
    ) -> None:
        """Register a new strategy for a specific action type.

        This method allows runtime extension of available actions.

        Args:
            action_type: Action type identifier
            strategy_class: Strategy class that implements ActionStrategy

        Raises:
            ValueError: If action_type already exists or strategy_class is invalid

        Example:
            >>> class CustomStrategy(ActionStrategy):
            ...     def execute(self, file_path, parent_path, target): pass
            ...     def validate(self, file_path, target): return True
            >>> ActionStrategyFactory.register_strategy('custom', CustomStrategy)
        """
        if action_type in cls._strategies:
            raise ValueError(f"Action type '{action_type}' is already registered")

        if not isinstance(strategy_class, type) or not issubclass(
            strategy_class, ActionStrategy
        ):
            raise ValueError("strategy_class must be a subclass of ActionStrategy")

        cls._strategies[action_type] = strategy_class

    @classmethod
    def unregister_strategy(cls, action_type: str) -> bool:
        """Unregister a strategy for a specific action type.

        Args:
            action_type: Action type to remove

        Returns:
            True if strategy was removed, False if it didn't exist

        Example:
            >>> ActionStrategyFactory.unregister_strategy('move')  # True
        """
        if action_type in cls._strategies:
            del cls._strategies[action_type]
            return True
        return False

    @classmethod
    def get_strategy_class(cls, action_type: str) -> Optional[Type[ActionStrategy]]:
        """Get the strategy class for a specific action type.

        This is useful for introspection or advanced use cases.

        Args:
            action_type: Action type to look up

        Returns:
            Strategy class or None if not found
        """
        return cls._strategies.get(action_type)

    @classmethod
    def get_strategy_info(cls) -> Dict[str, str]:
        """Get information about all registered strategies.

        Returns:
            Dictionary mapping action types to strategy class names
        """
        return {
            action_type: strategy_class.__name__
            for action_type, strategy_class in cls._strategies.items()
        }
