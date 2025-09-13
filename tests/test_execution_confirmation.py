"""
Unit tests for the confirmation handlers.
"""

from unittest.mock import patch

from unclutter_directory.execution.confirmation import (
    AutomaticConfirmationHandler,
    DryRunConfirmationHandler,
)


def test_dry_run_handler_delete():
    """Test DryRunConfirmationHandler for delete actions"""
    handler = DryRunConfirmationHandler()

    with patch("unclutter_directory.execution.confirmation.logger.info") as mock_logger:
        result = handler.should_execute(
            context_info="test file",
            prompt_template="",
            cache_key=None,
            action_type="delete",
        )

        # Should log the dry run action
        mock_logger.assert_called_once_with("[DRY RUN] Would delete for test file")
        # Should always return False
        assert result is False


def test_dry_run_handler_non_delete():
    """Test DryRunConfirmationHandler for non-delete actions"""
    handler = DryRunConfirmationHandler()

    with patch("unclutter_directory.execution.confirmation.logger.info") as mock_logger:
        result = handler.should_execute(
            context_info="test file",
            prompt_template="",
            cache_key=None,
            action_type="move",
        )

        # Should log the dry run action with the action type
        mock_logger.assert_called_once_with("[DRY RUN] Would move for test file")
        # Should always return False
        assert result is False


def test_automatic_handler_delete_true():
    """Test AutomaticConfirmationHandler with always_confirm=True for delete actions"""
    handler = AutomaticConfirmationHandler(always_confirm=True)

    result = handler.should_execute(
        context_info="test file",
        prompt_template="",
        cache_key=None,
        action_type="delete",
    )

    # Should return True when always_confirm is True
    assert result is True


def test_automatic_handler_delete_false():
    """Test AutomaticConfirmationHandler with always_confirm=False for delete actions"""
    handler = AutomaticConfirmationHandler(always_confirm=False)

    with patch("unclutter_directory.execution.confirmation.logger.info") as mock_logger:
        result = handler.should_execute(
            context_info="test file",
            prompt_template="",
            cache_key=None,
            action_type="delete",
        )

        # Should log the skip message
        mock_logger.assert_called_once_with(
            "Skipping delete action for test file (automatic mode)"
        )
        # Should return False when always_confirm is False
        assert result is False


def test_automatic_handler_non_delete():
    """Test AutomaticConfirmationHandler for non-delete actions"""
    handler_true = AutomaticConfirmationHandler(always_confirm=True)
    handler_false = AutomaticConfirmationHandler(always_confirm=False)

    # Non-delete actions should always return True regardless of always_confirm
    result1 = handler_true.should_execute(
        context_info="test file", prompt_template="", cache_key=None, action_type="move"
    )

    result2 = handler_false.should_execute(
        context_info="test file",
        prompt_template="",
        cache_key=None,
        action_type="compress",
    )

    assert result1 is True
    assert result2 is True
