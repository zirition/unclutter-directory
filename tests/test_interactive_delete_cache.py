from pathlib import Path
from unittest.mock import patch

from unclutter_directory.execution.delete_strategy import InteractiveDeleteStrategy


def test_interactive_delete_strategy_cache_all():
    """Test that 'all' response is cached and reused"""
    strategy = InteractiveDeleteStrategy()

    # Mock the input to return 'a' (all) on the first call
    with patch("builtins.input", return_value="a"):
        result1 = strategy.should_delete_directory(
            Path("/test/dir1"), Path("/test/archive1.zip")
        )

    # On subsequent calls, it should return True without asking for input
    with patch("builtins.input") as mock_input:
        result2 = strategy.should_delete_directory(
            Path("/test/dir2"), Path("/test/archive2.zip")
        )
        # Input should not be called again
        mock_input.assert_not_called()

    assert result1 is True
    assert result2 is True


def test_interactive_delete_strategy_cache_never():
    """Test that 'never' response is cached and reused"""
    strategy = InteractiveDeleteStrategy()

    # Mock the input to return 'never' on the first call
    with patch("builtins.input", return_value="never"):
        result1 = strategy.should_delete_directory(
            Path("/test/dir1"), Path("/test/archive1.zip")
        )

    # On subsequent calls, it should return False without asking for input
    with patch("builtins.input") as mock_input:
        result2 = strategy.should_delete_directory(
            Path("/test/dir2"), Path("/test/archive2.zip")
        )
        # Input should not be called again
        mock_input.assert_not_called()

    assert result1 is False
    assert result2 is False


def test_interactive_delete_strategy_no_cache_for_yes_no():
    """Test that 'yes' and 'no' responses are not cached"""
    strategy = InteractiveDeleteStrategy()

    # Mock the input to return 'y' (yes) on the first call
    with patch("builtins.input", return_value="y"):
        result1 = strategy.should_delete_directory(
            Path("/test/dir1"), Path("/test/archive1.zip")
        )

    # On subsequent calls, it should ask for input again
    with patch("builtins.input", return_value="n") as mock_input:
        result2 = strategy.should_delete_directory(
            Path("/test/dir2"), Path("/test/archive2.zip")
        )
        # Input should be called again
        mock_input.assert_called_once()

    assert result1 is True
    assert result2 is False
