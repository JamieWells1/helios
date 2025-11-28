"""
Simple mean reversion strategy.

Buy when price drops below 20-period SMA.
Sell when price returns above SMA or hits profit target.
"""

from typing import Dict, Any, Optional
from .base import BaseStrategy
from ..utils.logging import get_logger

logger = get_logger(__name__)


class MeanReversionStrategy(BaseStrategy):
    """
    Mean reversion: Buy dips below moving average, sell when price reverts.
    """

    def __init__(self, config: Dict[str, Any], candle_store: Optional[Any] = None):
        super().__init__(config)

        self.candle_store = candle_store
        self.sma_period = 20
        self.sma = None
        self.profit_target_pct = 2.0  # Take profit at 2%

        logger.info(f"MeanReversionStrategy: SMA({self.sma_period}), profit={self.profit_target_pct}%")

    def update(self, current_price: float) -> None:
        """Calculate 20-period SMA from OHLC data."""
        if not self.candle_store:
            logger.warning("No candle_store - cannot calculate SMA")
            return

        candles = self.candle_store.get_candles('1m', limit=self.sma_period + 10)

        if len(candles) < self.sma_period:
            logger.debug(f"Not enough candles: {len(candles)}/{self.sma_period}")
            return

        closes = [c.close for c in candles.candles]
        self.sma = self.calculate_sma(closes, self.sma_period)

        logger.debug(f"Price: ${current_price:.2f}, SMA: ${self.sma:.2f}")

    def should_buy(self, current_price: float) -> bool:
        """Buy when price drops 1% below SMA."""
        if self.sma is None:
            return False

        deviation_pct = ((current_price / self.sma) - 1) * 100

        if deviation_pct < -1.0:  # Price is 1%+ below SMA
            logger.info(f"BUY: Price ${current_price:.2f} is {deviation_pct:.2f}% below SMA ${self.sma:.2f}")
            return True

        return False

    def should_sell(self, current_price: float) -> bool:
        """Sell when price returns to SMA or hits profit target."""
        if self.sma is None or self.entry_price is None:
            return False

        profit_pct = ((current_price / self.entry_price) - 1) * 100

        # Take profit
        if profit_pct >= self.profit_target_pct:
            logger.info(f"SELL: Profit target hit {profit_pct:.2f}%")
            return True

        # Price returned above SMA (mean reversion complete)
        if current_price >= self.sma:
            logger.info(f"SELL: Price ${current_price:.2f} returned to SMA ${self.sma:.2f}")
            return True

        return False

    def calculate_sma(self, prices: list[float], period: int) -> float:
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        return sum(prices[-period:]) / period
