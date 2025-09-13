from unittest.mock import patch

from unclutter_directory.execution.confirmation import InteractiveConfirmationHandler


def test_interactive_confirmation_handler_cache_all():
    """Test that 'all' response is cached and reused for delete actions"""
    handler = InteractiveConfirmationHandler()

    # Mock the input to return 'a' (all) on the first call
    with patch("builtins.input", return_value="a"):
        result1 = handler.should_execute(
            context_info="test directory 1",
            prompt_template="Delete {context}? [Y/N/A/Never]: ",
            cache_key="key1",
            action_type="delete",
        )

    # On subsequent calls with same cache_key, it should return True without asking for input
    with patch("builtins.input") as mock_input:
        result2 = handler.should_execute(
            context_info="test directory 2",
            prompt_template="Delete {context}? [Y/N/A/Never]: ",
            cache_key="key1",
            action_type="delete",
        )
        # Input should not be called again
        mock_input.assert_not_called()

    assert result1 is True
    assert result2 is True


def test_interactive_confirmation_handler_cache_never():
    """Test that 'never' response is cached and reused for delete actions"""
    handler = InteractiveConfirmationHandler()

    # Mock the input to return 'never' on the first call
    with patch("builtins.input", return_value="never"):
        result1 = handler.should_execute(
            context_info="test directory 1",
            prompt_template="Delete {context}? [Y/N/A/Never]: ",
            cache_key="key1",
            action_type="delete",
        )

    # On subsequent calls with same cache_key, it should return False without asking for input
    with patch("builtins.input") as mock_input:
        result2 = handler.should_execute(
            context_info="test directory 2",
            prompt_template="Delete {context}? [Y/N/A/Never]: ",
            cache_key="key1",
            action_type="delete",
        )
        # Input should not be called again
        mock_input.assert_not_called()

    assert result1 is False
    assert result2 is False


def test_interactive_confirmation_handler_no_cache_for_yes_no():
    """Test that 'yes' and 'no' responses are not cached for delete actions"""
    handler = InteractiveConfirmationHandler()

    # Mock the input to return 'y' (yes) on the first call
    with patch("builtins.input", return_value="y"):
        result1 = handler.should_execute(
            context_info="test directory 1",
            prompt_template="Delete {context}? [Y/N/A/Never]: ",
            cache_key="key1",
            action_type="delete",
        )

    # On subsequent calls, it should ask for input again
    with patch("builtins.input", return_value="n") as mock_input:
        result2 = handler.should_execute(
            context_info="test directory 2",
            prompt_template="Delete {context}? [Y/N/A/Never]: ",
            cache_key="key2",  # Different key to force new prompt
            action_type="delete",
        )
        # Input should be called again
        mock_input.assert_called_once()

    assert result1 is True
    assert result2 is False


def test_interactive_confirmation_handler_non_delete_always_true():
    """Test that non-delete actions always return True without prompting"""
    handler = InteractiveConfirmationHandler()

    # Mock input to ensure it's never called
    with patch("builtins.input") as mock_input:
        result1 = handler.should_execute(
            context_info="test file",
            prompt_template="",  # Empty prompt for non-delete
            cache_key=None,
            action_type="move",
        )

        result2 = handler.should_execute(
            context_info="test file",
            prompt_template="",  # Empty prompt for non-delete
            cache_key=None,
            action_type="compress",
        )

        # Input should never be called for non-delete actions
        mock_input.assert_not_called()

    assert result1 is True
    assert result2 is True
