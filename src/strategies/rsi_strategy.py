"""
RSI-based trading strategy using OHLC data.
"""

from dataclasses import dataclass
from typing import Any

from .base import BaseStrategy
from ..data.models import CandleList
from ..indicators.technical import TechnicalIndicators, IndicatorConfig
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RSIStrategyConfig:
    """Configuration for RSI strategy."""
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    rsi_period: int = 14
    min_candles_required: int = 50


class RSIStrategy(BaseStrategy):
    """
    Simple RSI mean-reversion strategy.

    Buy when RSI drops below oversold threshold.
    Sell when RSI rises above overbought threshold.
    """

    def __init__(self, config: dict[str, Any], strategy_config: RSIStrategyConfig):
        """
        Initialize RSI strategy.

        Args:
            config: Main bot configuration
            strategy_config: RSI-specific configuration
        """
        super().__init__(config)
        self.strategy_config = strategy_config

        # Initialize technical indicators
        indicator_config = IndicatorConfig(rsi_period=strategy_config.rsi_period)
        self.indicators = TechnicalIndicators(indicator_config)

        logger.info(
            f"RSI Strategy initialized: "
            f"Oversold={strategy_config.rsi_oversold}, "
            f"Overbought={strategy_config.rsi_overbought}"
        )

    def update(self, current_price: float) -> None:
        """
        Update strategy state.

        Note: This strategy uses OHLC data, so current_price is not used.
        """
        pass

    def should_buy(self, current_price: float) -> bool:
        """
        Legacy interface - not used by this strategy.

        Use should_buy_candles() instead.
        """
        return False

    def should_sell(self, current_price: float) -> bool:
        """
        Legacy interface - not used by this strategy.

        Use should_sell_candles() instead.
        """
        return False

    def should_buy_candles(self, candles: CandleList) -> bool:
        """
        Determine if should buy based on candle data.

        Buy when RSI drops below oversold threshold.

        Args:
            candles: Historical candle data

        Returns:
            True if should buy, False otherwise
        """
        if len(candles) < self.strategy_config.min_candles_required:
            logger.warning(
                f"Insufficient candles: {len(candles)}/{self.strategy_config.min_candles_required}"
            )
            return False

        try:
            rsi = self.indicators.calculate_rsi(candles)

            current_price = candles.latest.close

            logger.debug(
                f"RSI: {rsi:.2f}, Price: ${current_price:.2f}, "
                f"Oversold threshold: {self.strategy_config.rsi_oversold}"
            )

            # Buy when oversold
            if rsi < self.strategy_config.rsi_oversold:
                logger.info(
                    f"BUY signal: RSI {rsi:.2f} < {self.strategy_config.rsi_oversold} "
                    f"(oversold)"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Error calculating buy signal: {e}")
            return False

    def should_sell_candles(self, candles: CandleList) -> bool:
        """
        Determine if should sell based on candle data.

        Sell when RSI rises above overbought threshold.

        Args:
            candles: Historical candle data

        Returns:
            True if should sell, False otherwise
        """
        if len(candles) < self.strategy_config.min_candles_required:
            return False

        try:
            rsi = self.indicators.calculate_rsi(candles)

            current_price = candles.latest.close

            logger.debug(
                f"RSI: {rsi:.2f}, Price: ${current_price:.2f}, "
                f"Overbought threshold: {self.strategy_config.rsi_overbought}"
            )

            # Sell when overbought
            if rsi > self.strategy_config.rsi_overbought:
                logger.info(
                    f"SELL signal: RSI {rsi:.2f} > {self.strategy_config.rsi_overbought} "
                    f"(overbought)"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Error calculating sell signal: {e}")
            return False
