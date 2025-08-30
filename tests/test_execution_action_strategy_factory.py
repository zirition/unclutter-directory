import unittest
from unittest.mock import Mock, patch

from unclutter_directory.execution.action_strategies import (
    ActionStrategy,
    CompressStrategy,
    DeleteStrategy,
    MoveStrategy,
)
from unclutter_directory.execution.action_strategy_factory import ActionStrategyFactory


class TestActionStrategyFactory(unittest.TestCase):
    """
    Comprehensive unit tests for ActionStrategyFactory class
    """

    def setUp(self):
        """Set up test environment"""
        self.factory = ActionStrategyFactory()

    def test_create_strategy_move(self):
        """Test creating MoveStrategy for move action"""
        logger = Mock()
        strategy = self.factory.create_strategy("move", logger)

        self.assertIsInstance(strategy, MoveStrategy)

    def test_create_strategy_delete(self):
        """Test creating DeleteStrategy for delete action"""
        logger = Mock()
        strategy = self.factory.create_strategy("delete", logger)

        self.assertIsInstance(strategy, DeleteStrategy)

    def test_create_strategy_compress(self):
        """Test creating CompressStrategy for compress action"""
        logger = Mock()
        strategy = self.factory.create_strategy("compress", logger)

        self.assertIsInstance(strategy, CompressStrategy)

    def test_create_strategy_invalid_type(self):
        """Test creating strategy with invalid action type"""
        logger = Mock()
        strategy = self.factory.create_strategy("invalid_action", logger)

        self.assertIsNone(strategy)

    def test_get_available_actions(self):
        """Test getting list of available actions"""
        actions = self.factory.get_available_actions()

        expected_actions = ["move", "delete", "compress"]
        self.assertEqual(actions, expected_actions)

    def test_is_action_supported_valid(self):
        """Test checking if valid actions are supported"""
        self.assertTrue(self.factory.is_action_supported("move"))
        self.assertTrue(self.factory.is_action_supported("delete"))
        self.assertTrue(self.factory.is_action_supported("compress"))

    def test_is_action_supported_invalid(self):
        """Test checking if invalid actions are supported"""
        self.assertFalse(self.factory.is_action_supported("invalid"))
        self.assertFalse(self.factory.is_action_supported("copy"))
        self.assertFalse(self.factory.is_action_supported("rename"))

    def test_register_strategy_success(self):
        """Test registering a new strategy successfully"""

        # Create a valid strategy class
        class MockStrategy(ActionStrategy):
            def execute(self, file_path, parent_path, target):
                pass

            def validate(self, file_path, target):
                return True

        # Register the strategy with a unique name
        strategy_name = "unique_mock_strategy"
        self.factory.register_strategy(strategy_name, MockStrategy)

        # Verify it can be created
        logger = Mock()
        strategy = self.factory.create_strategy(strategy_name, logger)
        self.assertIsInstance(strategy, MockStrategy)

    def test_register_strategy_invalid_type(self):
        """Test registering strategy with invalid type"""
        # Register invalid type should raise ValueError
        with self.assertRaises(ValueError):
            self.factory.register_strategy("non_callable", "not_a_class")

    def test_unregister_strategy_existing(self):
        """Test unregistering an existing strategy"""

        # Create a valid strategy class
        class MockStrategy(ActionStrategy):
            def execute(self, file_path, parent_path, target):
                pass

            def validate(self, file_path, target):
                return True

        # Register and then unregister with a unique name
        strategy_name = "unique_unregister_strategy"
        self.factory.register_strategy(strategy_name, MockStrategy)
        result = self.factory.unregister_strategy(strategy_name)
        self.assertTrue(result)

        # Verify it's no longer available
        self.assertFalse(self.factory.is_action_supported(strategy_name))
        self.assertIsNone(self.factory.create_strategy(strategy_name))

    def test_unregister_strategy_nonexistent(self):
        """Test unregistering a non-existent strategy"""
        result = self.factory.unregister_strategy("nonexistent")
        self.assertFalse(result)

    def test_get_strategy_class_existing(self):
        """Test getting strategy class for existing action"""
        strategy_class = self.factory.get_strategy_class("move")
        self.assertEqual(strategy_class, MoveStrategy)

    def test_get_strategy_class_nonexistent(self):
        """Test getting strategy class for non-existent action"""
        strategy_class = self.factory.get_strategy_class("nonexistent")
        self.assertIsNone(strategy_class)

    def test_get_strategy_info(self):
        """Test getting strategy info dictionary"""
        info = self.factory.get_strategy_info()

        # Verify info contains expected strategies
        self.assertIn("move", info)
        self.assertIn("delete", info)
        self.assertIn("compress", info)

        # Verify values are strategy class names (strings)
        self.assertEqual(info["move"], "MoveStrategy")
        self.assertEqual(info["delete"], "DeleteStrategy")
        self.assertEqual(info["compress"], "CompressStrategy")

    @patch("unclutter_directory.execution.action_strategies.logger")
    def test_create_strategy_without_logger(self, mock_logger):
        """Test creating strategy without providing logger (uses class attribute)"""
        strategy = self.factory.create_strategy("move")
        self.assertIsInstance(strategy, MoveStrategy)


class TestActionStrategyFactoryEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""

    def setUp(self):
        self.factory = ActionStrategyFactory()

    def test_get_strategy_class_case_sensitivity(self):
        """Test case sensitivity in get_strategy_class"""
        self.assertIsNone(self.factory.get_strategy_class("MOVE"))
        self.assertIsNotNone(self.factory.get_strategy_class("move"))

    def test_register_strategy_none_type(self):
        """Test registering None as strategy type"""
        with self.assertRaises(ValueError):
            self.factory.register_strategy("mock", None)

    def test_register_strategy_invalid_callable(self):
        """Test registering something that's callable but not a class"""

        def not_a_class():
            pass

        with self.assertRaises(ValueError):
            self.factory.register_strategy("mock", not_a_class)


if __name__ == "__main__":
    unittest.main(failfast=True)
