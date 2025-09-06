from unittest.mock import Mock, patch

import pytest

from unclutter_directory.execution.action_strategies import (
    ActionStrategy,
    CompressStrategy,
    DeleteStrategy,
    MoveStrategy,
)
from unclutter_directory.execution.action_strategy_factory import ActionStrategyFactory


@pytest.fixture
def factory():
    """Fixture para el ActionStrategyFactory"""
    return ActionStrategyFactory()


def test_create_strategy_move(factory):
    """Test creating MoveStrategy for move action"""
    logger = Mock()
    strategy = factory.create_strategy("move", logger)

    assert isinstance(strategy, MoveStrategy)


def test_create_strategy_delete(factory):
    """Test creating DeleteStrategy for delete action"""
    logger = Mock()
    strategy = factory.create_strategy("delete", logger)

    assert isinstance(strategy, DeleteStrategy)


def test_create_strategy_compress(factory):
    """Test creating CompressStrategy for compress action"""
    logger = Mock()
    strategy = factory.create_strategy("compress", logger)

    assert isinstance(strategy, CompressStrategy)


def test_create_strategy_invalid_type(factory):
    """Test creating strategy with invalid action type"""
    logger = Mock()
    strategy = factory.create_strategy("invalid_action", logger)

    assert strategy is None


def test_get_available_actions(factory):
    """Test getting list of available actions"""
    actions = factory.get_available_actions()

    expected_actions = ["move", "delete", "compress"]
    assert actions == expected_actions


def test_is_action_supported_valid(factory):
    """Test checking if valid actions are supported"""
    assert factory.is_action_supported("move")
    assert factory.is_action_supported("delete")
    assert factory.is_action_supported("compress")


def test_is_action_supported_invalid(factory):
    """Test checking if invalid actions are supported"""
    assert not factory.is_action_supported("invalid")
    assert not factory.is_action_supported("copy")
    assert not factory.is_action_supported("rename")


def test_register_strategy_success(factory):
    """Test registering a new strategy successfully"""

    # Create a valid strategy class
    class MockStrategy(ActionStrategy):
        def execute(self, file_path, parent_path, target):
            pass

        def validate(self, file_path, target):
            return True

    # Register the strategy with a unique name
    strategy_name = "unique_mock_strategy"
    factory.register_strategy(strategy_name, MockStrategy)

    # Verify it can be created
    logger = Mock()
    strategy = factory.create_strategy(strategy_name, logger)
    assert isinstance(strategy, MockStrategy)


def test_register_strategy_invalid_type(factory):
    """Test registering strategy with invalid type"""
    # Register invalid type should raise ValueError
    with pytest.raises(ValueError):
        factory.register_strategy("non_callable", "not_a_class")


def test_unregister_strategy_existing(factory):
    """Test unregistering an existing strategy"""

    # Create a valid strategy class
    class MockStrategy(ActionStrategy):
        def execute(self, file_path, parent_path, target):
            pass

        def validate(self, file_path, target):
            return True

    # Register and then unregister with a unique name
    strategy_name = "unique_unregister_strategy"
    factory.register_strategy(strategy_name, MockStrategy)
    result = factory.unregister_strategy(strategy_name)
    assert result is True

    # Verify it's no longer available
    assert not factory.is_action_supported(strategy_name)
    assert factory.create_strategy(strategy_name) is None


def test_unregister_strategy_nonexistent(factory):
    """Test unregistering a non-existent strategy"""
    result = factory.unregister_strategy("nonexistent")
    assert result is False


def test_get_strategy_class_existing(factory):
    """Test getting strategy class for existing action"""
    strategy_class = factory.get_strategy_class("move")
    assert strategy_class == MoveStrategy


def test_get_strategy_class_nonexistent(factory):
    """Test getting strategy class for non-existent action"""
    strategy_class = factory.get_strategy_class("nonexistent")
    assert strategy_class is None


def test_get_strategy_info(factory):
    """Test getting strategy info dictionary"""
    info = factory.get_strategy_info()

    # Verify info contains expected strategies
    assert "move" in info
    assert "delete" in info
    assert "compress" in info

    # Verify values are strategy class names (strings)
    assert info["move"] == "MoveStrategy"
    assert info["delete"] == "DeleteStrategy"
    assert info["compress"] == "CompressStrategy"


@patch("unclutter_directory.execution.action_strategies.logger")
def test_create_strategy_without_logger(mock_logger, factory):
    """Test creating strategy without providing logger (uses class attribute)"""
    strategy = factory.create_strategy("move")
    assert isinstance(strategy, MoveStrategy)


def test_get_strategy_class_case_sensitivity(factory):
    """Test case sensitivity in get_strategy_class"""
    assert factory.get_strategy_class("MOVE") is None
    assert factory.get_strategy_class("move") is not None


def test_register_strategy_none_type(factory):
    """Test registering None as strategy type"""
    with pytest.raises(ValueError):
        factory.register_strategy("mock", None)


def test_register_strategy_invalid_callable(factory):
    """Test registering something that's callable but not a class"""

    def not_a_class():
        pass

    with pytest.raises(ValueError):
        factory.register_strategy("mock", not_a_class)
