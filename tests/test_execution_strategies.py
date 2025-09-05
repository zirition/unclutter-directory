import unittest
from pathlib import Path
from typing import Dict
from unittest.mock import patch

from unclutter_directory.execution.strategies import (
    AutomaticStrategy,
    DryRunStrategy,
    InteractiveStrategy,
)


class TestInteractiveStrategy(unittest.TestCase):
    """Test cases for InteractiveStrategy class"""

    def setUp(self):
        self.strategy = InteractiveStrategy()
        self.test_file = Path("/tmp/test_file.txt")
        self.test_rule = {"name": "test_rule", "type": "delete_old_files"}
        self.rule_responses: Dict[int, str] = {}

    def test_non_delete_actions_always_execute(self):
        """Test that non-delete actions always return True"""
        result = self.strategy.should_execute_action(
            self.test_file,
            "move",  # Not delete
            self.test_rule,
            self.rule_responses,
        )

        self.assertTrue(result)
        # Should not affect rule_responses
        self.assertEqual(len(self.rule_responses), 0)

    @patch("builtins.input")
    def test_individual_yes_response(self, mock_input):
        """Test individual 'y' response - should not cache"""
        mock_input.return_value = "y"

        # First call
        result1 = self.strategy.should_execute_action(
            self.test_file, "delete", self.test_rule, self.rule_responses
        )

        # Should return True and cache should be empty (no caching for individual responses)
        self.assertTrue(result1)
        rule_id = id(self.test_rule)
        self.assertNotIn(rule_id, self.rule_responses)

    @patch("builtins.input")
    def test_individual_no_response(self, mock_input):
        """Test individual 'n' response - should not cache"""
        mock_input.return_value = "n"

        # First call
        result1 = self.strategy.should_execute_action(
            self.test_file, "delete", self.test_rule, self.rule_responses
        )

        # Should return False and cache should be empty
        self.assertFalse(result1)
        rule_id = id(self.test_rule)
        self.assertNotIn(rule_id, self.rule_responses)

    @patch("builtins.input")
    def test_apply_all_response_caches_and_executes(self, mock_input):
        """Test 'a' response - should cache and execute"""
        mock_input.return_value = "a"

        # First call
        result1 = self.strategy.should_execute_action(
            self.test_file, "delete", self.test_rule, self.rule_responses
        )

        # Should return True
        self.assertTrue(result1)

        # Should cache the response
        rule_id = str(id(self.test_rule))
        self.assertIn(rule_id, self.rule_responses)
        self.assertEqual(self.rule_responses[rule_id], "a")

    @patch("builtins.input")
    def test_never_response_caches_and_skips(self, mock_input):
        """Test 'never' response - should cache and skip execution"""
        mock_input.return_value = "never"

        # First call
        result1 = self.strategy.should_execute_action(
            self.test_file, "delete", self.test_rule, self.rule_responses
        )

        # Should return False
        self.assertFalse(result1)

        # Should cache the response
        rule_id = str(id(self.test_rule))
        self.assertIn(rule_id, self.rule_responses)
        self.assertEqual(self.rule_responses[rule_id], "never")

    @patch("builtins.input")
    def test_cached_apply_all_used_for_subsequent_files(self, mock_input):
        """Test that cached 'a' response is used for subsequent files with same rule"""
        id(self.test_rule)

        # First file - respond with 'a'
        mock_input.return_value = "a"
        result1 = self.strategy.should_execute_action(
            self.test_file, "delete", self.test_rule, self.rule_responses
        )

        # Mock a different file path to simulate same rule, different file
        second_file = Path("/tmp/second_file.txt")

        # Second file - should not prompt again
        # (mock_input is not called again because response is cached)
        result2 = self.strategy.should_execute_action(
            second_file, "delete", self.test_rule, self.rule_responses
        )

        # Both should execute (return True)
        self.assertTrue(result1)
        self.assertTrue(result2)

        # Should have been called only once (first file)
        self.assertEqual(mock_input.call_count, 1)
        mock_input.assert_called_once()

    @patch("builtins.input")
    def test_cached_never_used_for_subsequent_files(self, mock_input):
        """Test that cached 'never' response is used for subsequent files with same rule"""
        id(self.test_rule)

        # First file - respond with 'never'
        mock_input.return_value = "never"
        result1 = self.strategy.should_execute_action(
            self.test_file, "delete", self.test_rule, self.rule_responses
        )

        # Mock a different file path
        second_file = Path("/tmp/second_file.txt")

        # Second file - should not prompt again
        result2 = self.strategy.should_execute_action(
            second_file, "delete", self.test_rule, self.rule_responses
        )

        # Both should skip execution (return False)
        self.assertFalse(result1)
        self.assertFalse(result2)

        # Should have been called only once
        self.assertEqual(mock_input.call_count, 1)

    @patch("builtins.input")
    def test_individual_responses_prompt_each_time(self, mock_input):
        """Test that 'y' responses prompt for each file individually"""
        # Set up mock to return 'y' for both calls
        mock_input.side_effect = ["y", "y"]

        rule_id = id(self.test_rule)

        # First file
        result1 = self.strategy.should_execute_action(
            self.test_file, "delete", self.test_rule, self.rule_responses
        )

        # Different file with same rule
        second_file = Path("/tmp/second_file.txt")
        result2 = self.strategy.should_execute_action(
            second_file, "delete", self.test_rule, self.rule_responses
        )

        # Both execute
        self.assertTrue(result1)
        self.assertTrue(result2)

        # Should prompt twice (no caching)
        self.assertEqual(mock_input.call_count, 2)

        # No responses cached
        self.assertNotIn(rule_id, self.rule_responses)

    @patch("builtins.input")
    def test_empty_input_defaults_to_yes(self, mock_input):
        """Test empty input defaults to 'y'"""
        mock_input.return_value = ""  # Empty input

        result = self.strategy.should_execute_action(
            self.test_file, "delete", self.test_rule, self.rule_responses
        )

        self.assertTrue(result)
        rule_id = id(self.test_rule)
        # Empty input is treated as 'y' but still not cached
        self.assertNotIn(rule_id, self.rule_responses)

    @patch("builtins.input")
    def test_invalid_input_prompts_again(self, mock_input):
        """Test invalid input is rejected and prompts again"""
        mock_input.side_effect = ["invalid", "y"]

        with patch("builtins.print") as mock_print:
            result = self.strategy.should_execute_action(
                self.test_file, "delete", self.test_rule, self.rule_responses
            )

            # Should print error message
            mock_print.assert_called_with("Invalid response. Please try again.")

            # Final result should be True (y)
            self.assertTrue(result)

    @patch("builtins.input")
    def test_keyboard_interrupt_handling(self, mock_input):
        """Test KeyboardInterrupt is re-raised"""
        mock_input.side_effect = KeyboardInterrupt()

        with self.assertRaises(KeyboardInterrupt):
            self.strategy.should_execute_action(
                self.test_file, "delete", self.test_rule, self.rule_responses
            )

    @patch("builtins.input")
    def test_different_rules_have_separate_caches(self, mock_input):
        """Test that different rules maintain separate cache entries"""
        # Two different rules
        rule1 = {"name": "rule1", "type": "old_files"}
        rule2 = {"name": "rule2", "type": "temp_files"}

        mock_input.side_effect = ["a", "never"]

        # Rule 1 - apply all
        result1 = self.strategy.should_execute_action(
            self.test_file, "delete", rule1, self.rule_responses
        )

        # Rule 2 - never
        result2 = self.strategy.should_execute_action(
            self.test_file, "delete", rule2, self.rule_responses
        )

        self.assertTrue(result1)
        self.assertFalse(result2)

        # Both rules should be cached separately
        rule1_id = str(id(rule1))
        rule2_id = str(id(rule2))

        self.assertEqual(self.rule_responses[rule1_id], "a")
        self.assertEqual(self.rule_responses[rule2_id], "never")

    @patch("builtins.input")
    def test_prompt_message_format(self, mock_input):
        """Test the prompt message format"""
        mock_input.return_value = "y"

        self.strategy.should_execute_action(
            self.test_file, "delete", self.test_rule, self.rule_responses
        )

        expected_prompt = (
            f"Do you want to delete {self.test_file}? [Y(es)/N(o)/A(ll)/Never]: "
        )
        mock_input.assert_called_with(expected_prompt)


class TestDryRunStrategy(unittest.TestCase):
    """Test cases for DryRunStrategy class"""

    def setUp(self):
        self.strategy = DryRunStrategy()
        self.test_file = Path("/tmp/test_file.txt")
        self.test_rule = {"name": "test_rule", "type": "delete_old_files"}
        self.rule_responses: Dict[int, str] = {}

    def test_always_returns_false_for_any_action(self):
        """Test that DryRunStrategy always returns False regardless of action type"""
        actions = ["delete", "move", "compress", "copy", "rename"]

        for action in actions:
            with self.subTest(action=action):
                result = self.strategy.should_execute_action(
                    self.test_file, action, self.test_rule, self.rule_responses
                )
                self.assertFalse(
                    result, f"DryRun should return False for action: {action}"
                )

    def test_delete_specific_behavior(self):
        """Test specific delete action returns False"""
        result = self.strategy.should_execute_action(
            self.test_file, "delete", self.test_rule, self.rule_responses
        )
        self.assertFalse(result)

    def test_move_action_returns_false(self):
        """Test move action returns False"""
        result = self.strategy.should_execute_action(
            self.test_file, "move", self.test_rule, self.rule_responses
        )
        self.assertFalse(result)

    def test_compress_action_returns_false(self):
        """Test compress action returns False"""
        result = self.strategy.should_execute_action(
            self.test_file, "compress", self.test_rule, self.rule_responses
        )
        self.assertFalse(result)

    @patch("unclutter_directory.execution.strategies.logger")
    def test_log_match_with_target(self, mock_logger):
        """Test log_match method with target parameter"""
        target = "/some/directory"
        self.strategy.log_match(self.test_file, "move", target)

        expected_msg = f"[DRY RUN] Would execute: {self.test_file} | Action: move | Target: {target}"
        mock_logger.info.assert_called_once_with(expected_msg)

    @patch("unclutter_directory.execution.strategies.logger")
    def test_log_match_without_target(self, mock_logger):
        """Test log_match method without target parameter"""
        self.strategy.log_match(self.test_file, "delete")

        expected_msg = f"[DRY RUN] Would execute: {self.test_file} | Action: delete"
        mock_logger.info.assert_called_once_with(expected_msg)

    def test_does_not_modify_rule_responses(self):
        """Test that DryRunStrategy doesn't modify rule_responses"""
        initial_responses = self.rule_responses.copy()

        self.strategy.should_execute_action(
            self.test_file, "delete", self.test_rule, self.rule_responses
        )

        # rule_responses should remain unchanged
        self.assertEqual(self.rule_responses, initial_responses)


class TestAutomaticStrategy(unittest.TestCase):
    """Test cases for AutomaticStrategy class"""

    def setUp(self):
        self.test_file = Path("/tmp/test_file.txt")
        self.test_rule = {"name": "test_rule", "type": "delete_old_files"}
        self.rule_responses: Dict[int, str] = {}

    def test_init_stores_flags(self):
        """Test that constructor stores the flags correctly"""
        strategy = AutomaticStrategy(always_delete=True, never_delete=False)
        self.assertTrue(strategy.always_delete)
        self.assertFalse(strategy.never_delete)

    def test_always_delete_true_executes_deletions(self):
        """Test that when always_delete=True, delete actions return True"""
        strategy = AutomaticStrategy(always_delete=True, never_delete=False)

        result = strategy.should_execute_action(
            self.test_file, "delete", self.test_rule, self.rule_responses
        )
        self.assertTrue(result)

    def test_never_delete_true_skips_deletions(self):
        """Test that when never_delete=True, delete actions return False"""
        strategy = AutomaticStrategy(always_delete=False, never_delete=True)

        result = strategy.should_execute_action(
            self.test_file, "delete", self.test_rule, self.rule_responses
        )
        self.assertFalse(result)

    @patch("unclutter_directory.execution.strategies.logger")
    def test_never_delete_logs_message(self, mock_logger):
        """Test that never_delete mode logs appropriate message"""
        strategy = AutomaticStrategy(always_delete=False, never_delete=True)

        strategy.should_execute_action(
            self.test_file, "delete", self.test_rule, self.rule_responses
        )

        expected_msg = f"Skipping action for {self.test_file} (never-execute mode)"
        mock_logger.info.assert_called_once_with(expected_msg)

    def test_conflicting_flags_never_takes_precedence(self):
        """Test that never_delete takes precedence over always_delete"""
        strategy = AutomaticStrategy(always_delete=True, never_delete=True)

        result = strategy.should_execute_action(
            self.test_file, "delete", self.test_rule, self.rule_responses
        )
        self.assertFalse(result)  # never_delete wins

    def test_both_flags_false_returns_false(self):
        """Test that when both flags are False, delete returns False"""
        strategy = AutomaticStrategy(always_delete=False, never_delete=False)

        result = strategy.should_execute_action(
            self.test_file, "delete", self.test_rule, self.rule_responses
        )
        self.assertFalse(result)

    @patch("unclutter_directory.execution.strategies.logger")
    def test_both_flags_false_logs_warning(self, mock_logger):
        """Test that both flags False logs a warning"""
        strategy = AutomaticStrategy(always_delete=False, never_delete=False)

        strategy.should_execute_action(
            self.test_file, "delete", self.test_rule, self.rule_responses
        )

        expected_msg = (
            f"Automatic strategy without execution preference for {self.test_file}"
        )
        mock_logger.warning.assert_called_once_with(expected_msg)

    def test_non_delete_actions_always_execute(self):
        """Test that non-delete actions always return True regardless of flags"""
        actions = ["move", "compress", "copy", "rename"]

        for always_delete, never_delete in [
            (True, False),
            (False, True),
            (False, False),
        ]:
            strategy = AutomaticStrategy(always_delete, never_delete)

            for action in actions:
                with self.subTest(
                    action=action,
                    always_delete=always_delete,
                    never_delete=never_delete,
                ):
                    result = strategy.should_execute_action(
                        self.test_file, action, self.test_rule, self.rule_responses
                    )
                    self.assertTrue(
                        result, f"Non-delete action '{action}' should always execute"
                    )

    def test_delete_action_specific_cases(self):
        """Test specific delete action combinations"""
        test_cases = [
            # (always_delete, never_delete, expected_result)
            (True, False, True),  # Always delete
            (False, True, False),  # Never delete
            (True, True, False),  # Never takes precedence
            (False, False, False),  # No preference defaults to False
        ]

        for always_delete, never_delete, expected in test_cases:
            with self.subTest(always=always_delete, never=never_delete):
                strategy = AutomaticStrategy(always_delete, never_delete)
                result = strategy.should_execute_action(
                    self.test_file, "delete", self.test_rule, self.rule_responses
                )
                self.assertEqual(result, expected)

    def test_does_not_modify_rule_responses(self):
        """Test that AutomaticStrategy doesn't modify rule_responses"""
        strategy = AutomaticStrategy(always_delete=True, never_delete=False)
        initial_responses = self.rule_responses.copy()

        strategy.should_execute_action(
            self.test_file, "delete", self.test_rule, self.rule_responses
        )

        # rule_responses should remain unchanged
        self.assertEqual(self.rule_responses, initial_responses)


if __name__ == "__main__":
    unittest.main(failfast=True)
