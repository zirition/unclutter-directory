from pathlib import Path
from unittest.mock import patch

import pytest

from unclutter_directory.execution.strategies import (
    AutomaticStrategy,
    DryRunStrategy,
    InteractiveStrategy,
)


@pytest.fixture
def test_file():
    return Path("/tmp/test_file.txt")


@pytest.fixture
def test_rule():
    return {"name": "test_rule", "type": "delete_old_files"}


@pytest.fixture
def rule_responses():
    return {}


@pytest.fixture
def interactive_strategy():
    return InteractiveStrategy()


@pytest.fixture
def dryrun_strategy():
    return DryRunStrategy()


class TestInteractiveStrategy:
    """Test cases for InteractiveStrategy class"""

    def test_non_delete_actions_always_execute(
        self, interactive_strategy, test_file, test_rule, rule_responses
    ):
        """Test that non-delete actions always return True"""
        result = interactive_strategy.should_execute_action(
            test_file,
            "move",  # Not delete
            test_rule,
            rule_responses,
        )

        assert result
        # Should not affect rule_responses
        assert len(rule_responses) == 0

    @patch("builtins.input")
    def test_individual_yes_response(
        self, mock_input, interactive_strategy, test_file, test_rule, rule_responses
    ):
        """Test individual 'y' response - should not cache"""
        mock_input.return_value = "y"

        # First call
        result1 = interactive_strategy.should_execute_action(
            test_file, "delete", test_rule, rule_responses
        )

        # Should return True and cache should be empty (no caching for individual responses)
        assert result1
        rule_id = id(test_rule)
        assert rule_id not in rule_responses

    @patch("builtins.input")
    def test_individual_no_response(
        self, mock_input, interactive_strategy, test_file, test_rule, rule_responses
    ):
        """Test individual 'n' response - should not cache"""
        mock_input.return_value = "n"

        # First call
        result1 = interactive_strategy.should_execute_action(
            test_file, "delete", test_rule, rule_responses
        )

        # Should return False and cache should be empty
        assert not result1
        rule_id = id(test_rule)
        assert rule_id not in rule_responses

    @patch("builtins.input")
    def test_apply_all_response_caches_and_executes(
        self, mock_input, interactive_strategy, test_file, test_rule, rule_responses
    ):
        """Test 'a' response - should cache and execute"""
        mock_input.return_value = "a"

        # First call
        result1 = interactive_strategy.should_execute_action(
            test_file, "delete", test_rule, rule_responses
        )

        # Should return True
        assert result1

        # Should cache the response
        rule_id = str(id(test_rule))
        assert rule_id in rule_responses
        assert rule_responses[rule_id] == "a"

    @patch("builtins.input")
    def test_never_response_caches_and_skips(
        self, mock_input, interactive_strategy, test_file, test_rule, rule_responses
    ):
        """Test 'never' response - should cache and skip execution"""
        mock_input.return_value = "never"

        # First call
        result1 = interactive_strategy.should_execute_action(
            test_file, "delete", test_rule, rule_responses
        )

        # Should return False
        assert not result1

        # Should cache the response
        rule_id = str(id(test_rule))
        assert rule_id in rule_responses
        assert rule_responses[rule_id] == "never"

    @patch("builtins.input")
    def test_cached_apply_all_used_for_subsequent_files(
        self, mock_input, interactive_strategy, test_file, test_rule, rule_responses
    ):
        """Test that cached 'a' response is used for subsequent files with same rule"""
        id(test_rule)

        # First file - respond with 'a'
        mock_input.return_value = "a"
        result1 = interactive_strategy.should_execute_action(
            test_file, "delete", test_rule, rule_responses
        )

        # Mock a different file path to simulate same rule, different file
        second_file = Path("/tmp/second_file.txt")

        # Second file - should not prompt again
        # (mock_input is not called again because response is cached)
        result2 = interactive_strategy.should_execute_action(
            second_file, "delete", test_rule, rule_responses
        )

        # Both should execute (return True)
        assert result1
        assert result2

        # Should have been called only once (first file)
        assert mock_input.call_count == 1
        mock_input.assert_called_once()

    @patch("builtins.input")
    def test_cached_never_used_for_subsequent_files(
        self, mock_input, interactive_strategy, test_file, test_rule, rule_responses
    ):
        """Test that cached 'never' response is used for subsequent files with same rule"""
        id(test_rule)

        # First file - respond with 'never'
        mock_input.return_value = "never"
        result1 = interactive_strategy.should_execute_action(
            test_file, "delete", test_rule, rule_responses
        )

        # Mock a different file path
        second_file = Path("/tmp/second_file.txt")

        # Second file - should not prompt again
        result2 = interactive_strategy.should_execute_action(
            second_file, "delete", test_rule, rule_responses
        )

        # Both should skip execution (return False)
        assert not result1
        assert not result2

        # Should have been called only once
        assert mock_input.call_count == 1

    @patch("builtins.input")
    def test_individual_responses_prompt_each_time(
        self, mock_input, interactive_strategy, test_file, test_rule, rule_responses
    ):
        """Test that 'y' responses prompt for each file individually"""
        # Set up mock to return 'y' for both calls
        mock_input.side_effect = ["y", "y"]

        rule_id = id(test_rule)

        # First file
        result1 = interactive_strategy.should_execute_action(
            test_file, "delete", test_rule, rule_responses
        )

        # Different file with same rule
        second_file = Path("/tmp/second_file.txt")
        result2 = interactive_strategy.should_execute_action(
            second_file, "delete", test_rule, rule_responses
        )

        # Both execute
        assert result1
        assert result2

        # Should prompt twice (no caching)
        assert mock_input.call_count == 2

        # No responses cached
        assert rule_id not in rule_responses

    @patch("builtins.input")
    def test_empty_input_defaults_to_yes(
        self, mock_input, interactive_strategy, test_file, test_rule, rule_responses
    ):
        """Test empty input defaults to 'y'"""
        mock_input.return_value = ""  # Empty input

        result = interactive_strategy.should_execute_action(
            test_file, "delete", test_rule, rule_responses
        )

        assert result
        rule_id = id(test_rule)
        # Empty input is treated as 'y' but still not cached
        assert rule_id not in rule_responses

    @patch("builtins.input")
    def test_invalid_input_prompts_again(
        self, mock_input, interactive_strategy, test_file, test_rule, rule_responses
    ):
        """Test invalid input is rejected and prompts again"""
        mock_input.side_effect = ["invalid", "y"]

        with patch("builtins.print") as mock_print:
            result = interactive_strategy.should_execute_action(
                test_file, "delete", test_rule, rule_responses
            )

            # Should print error message
            mock_print.assert_called_with("Invalid response. Please try again.")

            # Final result should be True (y)
            assert result

    @patch("builtins.input")
    def test_keyboard_interrupt_handling(
        self, mock_input, interactive_strategy, test_file, test_rule, rule_responses
    ):
        """Test KeyboardInterrupt is re-raised"""
        mock_input.side_effect = KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            interactive_strategy.should_execute_action(
                test_file, "delete", test_rule, rule_responses
            )

    @patch("builtins.input")
    def test_different_rules_have_separate_caches(
        self, mock_input, interactive_strategy, test_file, rule_responses
    ):
        """Test that different rules maintain separate cache entries"""
        # Two different rules
        rule1 = {"name": "rule1", "type": "old_files"}
        rule2 = {"name": "rule2", "type": "temp_files"}

        mock_input.side_effect = ["a", "never"]

        # Rule 1 - apply all
        result1 = interactive_strategy.should_execute_action(
            test_file, "delete", rule1, rule_responses
        )

        # Rule 2 - never
        result2 = interactive_strategy.should_execute_action(
            test_file, "delete", rule2, rule_responses
        )

        assert result1
        assert not result2

        # Both rules should be cached separately
        rule1_id = str(id(rule1))
        rule2_id = str(id(rule2))

        assert rule_responses[rule1_id] == "a"
        assert rule_responses[rule2_id] == "never"

    @patch("builtins.input")
    def test_prompt_message_format(
        self, mock_input, interactive_strategy, test_file, test_rule, rule_responses
    ):
        """Test the prompt message format"""
        mock_input.return_value = "y"

        interactive_strategy.should_execute_action(
            test_file, "delete", test_rule, rule_responses
        )

        expected_prompt = (
            f"Do you want to delete {test_file}? [Y(es)/N(o)/A(ll)/Never]: "
        )
        mock_input.assert_called_with(expected_prompt)


class TestDryRunStrategy:
    """Test cases for DryRunStrategy class"""

    def test_always_returns_false_for_any_action(
        self, dryrun_strategy, test_file, test_rule, rule_responses
    ):
        """Test that DryRunStrategy always returns False regardless of action type"""
        actions = ["delete", "move", "compress", "copy", "rename"]

        for action in actions:
            result = dryrun_strategy.should_execute_action(
                test_file, action, test_rule, rule_responses
            )
            assert not result, f"DryRun should return False for action: {action}"

    def test_delete_specific_behavior(
        self, dryrun_strategy, test_file, test_rule, rule_responses
    ):
        """Test specific delete action returns False"""
        result = dryrun_strategy.should_execute_action(
            test_file, "delete", test_rule, rule_responses
        )
        assert not result

    def test_move_action_returns_false(
        self, dryrun_strategy, test_file, test_rule, rule_responses
    ):
        """Test move action returns False"""
        result = dryrun_strategy.should_execute_action(
            test_file, "move", test_rule, rule_responses
        )
        assert not result

    def test_compress_action_returns_false(
        self, dryrun_strategy, test_file, test_rule, rule_responses
    ):
        """Test compress action returns False"""
        result = dryrun_strategy.should_execute_action(
            test_file, "compress", test_rule, rule_responses
        )
        assert not result

    @patch("unclutter_directory.execution.strategies.logger")
    def test_log_match_with_target(self, mock_logger, dryrun_strategy, test_file):
        """Test log_match method with target parameter"""
        target = "/some/directory"
        dryrun_strategy.log_match(test_file, "move", target)

        expected_msg = (
            f"[DRY RUN] Would execute: {test_file} | Action: move | Target: {target}"
        )
        mock_logger.info.assert_called_once_with(expected_msg)

    @patch("unclutter_directory.execution.strategies.logger")
    def test_log_match_without_target(self, mock_logger, dryrun_strategy, test_file):
        """Test log_match method without target parameter"""
        dryrun_strategy.log_match(test_file, "delete")

        expected_msg = f"[DRY RUN] Would execute: {test_file} | Action: delete"
        mock_logger.info.assert_called_once_with(expected_msg)

    def test_does_not_modify_rule_responses(
        self, dryrun_strategy, test_file, test_rule, rule_responses
    ):
        """Test that DryRunStrategy doesn't modify rule_responses"""
        initial_responses = rule_responses.copy()

        dryrun_strategy.should_execute_action(
            test_file, "delete", test_rule, rule_responses
        )

        # rule_responses should remain unchanged
        assert rule_responses == initial_responses


class TestAutomaticStrategy:
    """Test cases for AutomaticStrategy class"""

    @pytest.fixture
    def test_file(self):
        return Path("/tmp/test_file.txt")

    @pytest.fixture
    def test_rule(self):
        return {"name": "test_rule", "type": "delete_old_files"}

    @pytest.fixture
    def rule_responses(self):
        return {}

    def test_init_stores_flags(self):
        """Test that constructor stores the flags correctly"""
        strategy = AutomaticStrategy(always_delete=True, never_delete=False)
        assert strategy.always_delete
        assert not strategy.never_delete

    def test_always_delete_true_executes_deletions(
        self, test_file, test_rule, rule_responses
    ):
        """Test that when always_delete=True, delete actions return True"""
        strategy = AutomaticStrategy(always_delete=True, never_delete=False)

        result = strategy.should_execute_action(
            test_file, "delete", test_rule, rule_responses
        )
        assert result

    def test_never_delete_true_skips_deletions(
        self, test_file, test_rule, rule_responses
    ):
        """Test that when never_delete=True, delete actions return False"""
        strategy = AutomaticStrategy(always_delete=False, never_delete=True)

        result = strategy.should_execute_action(
            test_file, "delete", test_rule, rule_responses
        )
        assert not result

    @patch("unclutter_directory.execution.strategies.logger")
    def test_never_delete_logs_message(
        self, mock_logger, test_file, test_rule, rule_responses
    ):
        """Test that never_delete mode logs appropriate message"""
        strategy = AutomaticStrategy(always_delete=False, never_delete=True)

        strategy.should_execute_action(test_file, "delete", test_rule, rule_responses)

        expected_msg = f"Skipping action for {test_file} (never-execute mode)"
        mock_logger.info.assert_called_once_with(expected_msg)

    def test_conflicting_flags_never_takes_precedence(
        self, test_file, test_rule, rule_responses
    ):
        """Test that never_delete takes precedence over always_delete"""
        strategy = AutomaticStrategy(always_delete=True, never_delete=True)

        result = strategy.should_execute_action(
            test_file, "delete", test_rule, rule_responses
        )
        assert not result  # never_delete wins

    def test_both_flags_false_returns_false(self, test_file, test_rule, rule_responses):
        """Test that when both flags are False, delete returns False"""
        strategy = AutomaticStrategy(always_delete=False, never_delete=False)

        result = strategy.should_execute_action(
            test_file, "delete", test_rule, rule_responses
        )
        assert not result

    @patch("unclutter_directory.execution.strategies.logger")
    def test_both_flags_false_logs_warning(
        self, mock_logger, test_file, test_rule, rule_responses
    ):
        """Test that both flags False logs a warning"""
        strategy = AutomaticStrategy(always_delete=False, never_delete=False)

        strategy.should_execute_action(test_file, "delete", test_rule, rule_responses)

        expected_msg = (
            f"Automatic strategy without execution preference for {test_file}"
        )
        mock_logger.warning.assert_called_once_with(expected_msg)

    def test_non_delete_actions_always_execute(
        self, test_file, test_rule, rule_responses
    ):
        """Test that non-delete actions always return True regardless of flags"""
        actions = ["move", "compress", "copy", "rename"]

        for always_delete, never_delete in [
            (True, False),
            (False, True),
            (False, False),
        ]:
            strategy = AutomaticStrategy(always_delete, never_delete)

            for action in actions:
                result = strategy.should_execute_action(
                    test_file, action, test_rule, rule_responses
                )
                assert result, f"Non-delete action '{action}' should always execute"

    def test_delete_action_specific_cases(self, test_file, test_rule, rule_responses):
        """Test specific delete action combinations"""
        test_cases = [
            # (always_delete, never_delete, expected_result)
            (True, False, True),  # Always delete
            (False, True, False),  # Never delete
            (True, True, False),  # Never takes precedence
            (False, False, False),  # No preference defaults to False
        ]

        for always_delete, never_delete, expected in test_cases:
            strategy = AutomaticStrategy(always_delete, never_delete)
            result = strategy.should_execute_action(
                test_file, "delete", test_rule, rule_responses
            )
            assert result == expected

    def test_does_not_modify_rule_responses(self, test_file, test_rule, rule_responses):
        """Test that AutomaticStrategy doesn't modify rule_responses"""
        strategy = AutomaticStrategy(always_delete=True, never_delete=False)
        initial_responses = rule_responses.copy()

        strategy.should_execute_action(test_file, "delete", test_rule, rule_responses)

        # rule_responses should remain unchanged
        assert rule_responses == initial_responses
