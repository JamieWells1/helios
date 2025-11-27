"""
Abstract base class for trading strategies.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from enum import Enum

from ..utils.logging import get_logger

logger = get_logger(__name__)


class Signal(Enum):
    """Trading signals."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class Position(Enum):
    """Position states."""
    FLAT = "flat"
    LONG = "long"


class BaseStrategy(ABC):
    """
    Abstract base class that all trading strategies must implement.

    Strategies receive market data and return trading signals.
    They maintain state about current position but do not interact
    with the blockchain directly.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize strategy with configuration.

        Args:
            config: Configuration dictionary with strategy parameters
        """
        self.config = config
        self.position = Position.FLAT
        self.entry_price: Optional[float] = None
        self.strategy_state: Dict[str, Any] = {}

        logger.info(f"Initialized strategy: {self.__class__.__name__}")

    @abstractmethod
    def should_buy(self, current_price: float) -> bool:
        """
        Determine if a buy signal should be generated.

        Args:
            current_price: Current market price

        Returns:
            True if should buy, False otherwise
        """
        pass

    @abstractmethod
    def should_sell(self, current_price: float) -> bool:
        """
        Determine if a sell signal should be generated.

        Args:
            current_price: Current market price

        Returns:
            True if should sell, False otherwise
        """
        pass

    @abstractmethod
    def update(self, current_price: float) -> None:
        """
        Update strategy state with new market data.

        Args:
            current_price: Current market price
        """
        pass

    def get_signal(self, current_price: float) -> Signal:
        """
        Get trading signal for current price.

        Args:
            current_price: Current market price

        Returns:
            Trading signal (BUY, SELL, or HOLD)
        """
        self.update(current_price)

        if self.position == Position.FLAT and self.should_buy(current_price):
            logger.info(f"BUY signal generated at price ${current_price:.4f}")
            return Signal.BUY

        if self.position == Position.LONG and self.should_sell(current_price):
            logger.info(f"SELL signal generated at price ${current_price:.4f}")
            return Signal.SELL

        return Signal.HOLD

    def on_buy(self, entry_price: float) -> None:
        """
        Called when a buy order is executed.

        Args:
            entry_price: Price at which position was entered
        """
        self.position = Position.LONG
        self.entry_price = entry_price
        logger.info(f"Position opened: LONG at ${entry_price:.4f}")

    def on_sell(self, exit_price: float) -> None:
        """
        Called when a sell order is executed.

        Args:
            exit_price: Price at which position was exited
        """
        if self.entry_price:
            pnl = exit_price - self.entry_price
            pnl_percent = (pnl / self.entry_price) * 100
            logger.info(
                f"Position closed: Entry=${self.entry_price:.4f}, "
                f"Exit=${exit_price:.4f}, "
                f"P&L=${pnl:.4f} ({pnl_percent:+.2f}%)"
            )

        self.position = Position.FLAT
        self.entry_price = None

    def get_position_size(self, available_balance: float) -> float:
        """
        Calculate position size based on available balance.

        Args:
            available_balance: Available USDC balance

        Returns:
            Position size in USDC
        """
        position_size = self.config.get('position_size_usdc', 100.0)
        max_position_size = self.config.get('max_position_size_usdc', 1000.0)

        return min(position_size, available_balance, max_position_size)

    def get_state(self) -> Dict[str, Any]:
        """
        Get current strategy state for persistence.

        Returns:
            Dictionary containing strategy state
        """
        return {
            'position': self.position.value,
            'entry_price': self.entry_price,
            'strategy_state': self.strategy_state
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        """
        Load strategy state from persistence.

        Args:
            state: Dictionary containing saved strategy state
        """
        try:
            position_str = state.get('position', 'flat')
            self.position = Position(position_str)
            self.entry_price = state.get('entry_price')
            self.strategy_state = state.get('strategy_state', {})

            logger.info(f"Strategy state loaded: position={self.position.value}")
        except Exception as e:
            logger.error(f"Failed to load strategy state: {e}")
            logger.warning("Using default state")
