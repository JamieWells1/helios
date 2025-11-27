"""
Skeleton strategy template for implementing custom trading strategies.

Copy this file and implement your own logic.
"""

from typing import Dict, Any

from .base import BaseStrategy
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SkeletonStrategy(BaseStrategy):
    """
    A skeleton strategy template to get you started.

    Implement the three core methods:
    - update(): Process new price data
    - should_buy(): Determine when to enter a position
    - should_sell(): Determine when to exit a position
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize your strategy.

        Args:
            config: Configuration dictionary from the main bot
        """
        super().__init__(config)

        # Initialize your strategy state here
        # Example: self.price_history = []
        # Example: self.indicators = {}

        logger.info("SkeletonStrategy initialized")

    def update(self, current_price: float) -> None:
        """
        Update strategy with new price data.

        This is called on every iteration before signals are checked.
        Use this to:
        - Store price history
        - Calculate indicators
        - Update internal state

        Args:
            current_price: Current market price
        """
        # Store price data, calculate indicators, etc.
        # Example: self.price_history.append(current_price)

        logger.debug(f"Updated with price: ${current_price:.4f}")

    def should_buy(self, current_price: float) -> bool:
        """
        Determine if a buy signal should be generated.

        This is only called when the bot is currently FLAT (no position).
        Return True to enter a LONG position.

        Args:
            current_price: Current market price

        Returns:
            True if should buy, False otherwise
        """
        # Implement your buy logic here
        # Example: return current_price < some_threshold

        return False

    def should_sell(self, current_price: float) -> bool:
        """
        Determine if a sell signal should be generated.

        This is only called when the bot is currently LONG.
        Return True to exit the position.

        Args:
            current_price: Current market price

        Returns:
            True if should sell, False otherwise
        """
        # Implement your sell logic here
        # Example: return current_price > entry_price * 1.05  # 5% profit target

        return False
