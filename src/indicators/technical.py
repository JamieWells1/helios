"""
Core technical indicators using pandas and ta library.
"""

from dataclasses import dataclass
from typing import List

import pandas as pd
import ta

from ..data.models import CandleList, IndicatorValues
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class IndicatorConfig:
    """Configuration for technical indicators."""
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    bb_period: int = 20
    bb_std: float = 2.0


class TechnicalIndicators:
    """
    Calculate technical indicators from candle data.

    Provides RSI, MACD, and Bollinger Bands.
    """

    def __init__(self, config: IndicatorConfig = IndicatorConfig()):
        """
        Initialize with configuration.

        Args:
            config: Indicator configuration parameters
        """
        self.config = config
        logger.info(
            f"Technical indicators initialized: "
            f"RSI({config.rsi_period}), "
            f"MACD({config.macd_fast},{config.macd_slow},{config.macd_signal}), "
            f"BB({config.bb_period},{config.bb_std})"
        )

    def calculate_all(self, candles: CandleList) -> IndicatorValues:
        """
        Calculate all indicators for given candles.

        Args:
            candles: CandleList with historical data

        Returns:
            IndicatorValues with all calculated indicators

        Raises:
            ValueError: If insufficient candle data
        """
        min_required = max(
            self.config.rsi_period,
            self.config.macd_slow + self.config.macd_signal,
            self.config.bb_period
        )

        if len(candles) < min_required:
            raise ValueError(
                f"Insufficient candles: need {min_required}, got {len(candles)}"
            )

        df = self._to_dataframe(candles)

        rsi = self._calculate_rsi(df)
        macd_line, macd_signal, macd_hist = self._calculate_macd(df)
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(df)

        return IndicatorValues(
            rsi=rsi,
            macd_line=macd_line,
            macd_signal=macd_signal,
            macd_histogram=macd_hist,
            bb_upper=bb_upper,
            bb_middle=bb_middle,
            bb_lower=bb_lower
        )

    def _to_dataframe(self, candles: CandleList) -> pd.DataFrame:
        """Convert CandleList to pandas DataFrame."""
        return pd.DataFrame({
            'timestamp': [c.timestamp for c in candles],
            'open': [c.open for c in candles],
            'high': [c.high for c in candles],
            'low': [c.low for c in candles],
            'close': [c.close for c in candles],
            'volume': [c.volume for c in candles]
        })

    def _calculate_rsi(self, df: pd.DataFrame) -> float:
        """
        Calculate Relative Strength Index.

        Returns:
            Current RSI value (0-100)
        """
        rsi_series = ta.momentum.rsi(
            close=df['close'],
            window=self.config.rsi_period
        )
        return float(rsi_series.iloc[-1])

    def _calculate_macd(self, df: pd.DataFrame) -> tuple[float, float, float]:
        """
        Calculate MACD indicator.

        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        macd = ta.trend.MACD(
            close=df['close'],
            window_fast=self.config.macd_fast,
            window_slow=self.config.macd_slow,
            window_sign=self.config.macd_signal
        )

        macd_line = float(macd.macd().iloc[-1])
        signal_line = float(macd.macd_signal().iloc[-1])
        histogram = float(macd.macd_diff().iloc[-1])

        return macd_line, signal_line, histogram

    def _calculate_bollinger_bands(
        self,
        df: pd.DataFrame
    ) -> tuple[float, float, float]:
        """
        Calculate Bollinger Bands.

        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        bb = ta.volatility.BollingerBands(
            close=df['close'],
            window=self.config.bb_period,
            window_dev=self.config.bb_std
        )

        upper = float(bb.bollinger_hband().iloc[-1])
        middle = float(bb.bollinger_mavg().iloc[-1])
        lower = float(bb.bollinger_lband().iloc[-1])

        return upper, middle, lower

    def calculate_rsi(self, candles: CandleList) -> float:
        """
        Calculate only RSI (faster if you only need one indicator).

        Args:
            candles: CandleList with historical data

        Returns:
            Current RSI value
        """
        df = self._to_dataframe(candles)
        return self._calculate_rsi(df)

    def calculate_ema(self, prices: List[float], period: int) -> float:
        """
        Calculate Exponential Moving Average.

        Args:
            prices: List of prices
            period: EMA period

        Returns:
            Current EMA value
        """
        series = pd.Series(prices)
        ema = series.ewm(span=period, adjust=False).mean()
        return float(ema.iloc[-1])

    def calculate_sma(self, prices: List[float], period: int) -> float:
        """
        Calculate Simple Moving Average.

        Args:
            prices: List of prices
            period: SMA period

        Returns:
            Current SMA value
        """
        if len(prices) < period:
            return sum(prices) / len(prices)
        return sum(prices[-period:]) / period
