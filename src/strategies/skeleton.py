"""
Skeleton strategy template for implementing custom trading strategies.

This is your starting point. Copy this file, rename it, and implement your own logic.

QUICK START:
1. Copy this file to a new file (e.g., my_strategy.py)
2. Rename the class (e.g., MyStrategy)
3. Implement the three core methods: update(), should_buy(), should_sell()
4. Instantiate your strategy and pass it to bot.initialize(strategy=MyStrategy(config))

WHAT DATA DO YOU HAVE ACCESS TO?
- current_price: Real-time SOL/USDC price (updated every CHECK_INTERVAL_SECONDS)
- self.config: Bot configuration dictionary with all .env variables
- self.position: Current position state (Position.FLAT or Position.LONG)
- self.entry_price: Price you entered at (if LONG, else None)
- self.strategy_state: Dictionary to store your own state between iterations

ACCESSING OHLC DATA (for technical indicators):
If USE_OHLC_DATA=true in .env, you have access to 10,000 1-minute candles.
Access them through the bot's candle store in main.py, or fetch directly in your strategy.

Example:
    from src.data.candle_store import CandleStore

    def __init__(self, config, candle_store):
        super().__init__(config)
        self.candle_store = candle_store

    def calculate_rsi(self, period=14):
        candles = self.candle_store.get_candles('1m', limit=period + 100)
        # ... calculate RSI from candles ...
        return rsi_value
"""

from typing import Dict, Any, Optional
from .base import BaseStrategy
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SkeletonStrategy(BaseStrategy):
    """
    Skeleton strategy template - copy and customize this.

    The bot calls these methods in this order each iteration:
    1. update(current_price) - Update your state/indicators
    2. should_buy(current_price) - Check if you want to enter (if FLAT)
    3. should_sell(current_price) - Check if you want to exit (if LONG)

    STRATEGY FLOW:
    - Bot is FLAT → should_buy() returns True → Bot buys → Position becomes LONG
    - Bot is LONG → should_sell() returns True → Bot sells → Position becomes FLAT
    - Bot repeats every CHECK_INTERVAL_SECONDS (e.g., every 30 seconds)
    """

    def __init__(self, config: Dict[str, Any], candle_store: Optional[Any] = None):
        """
        Initialize your strategy with configuration and optional OHLC data access.

        Args:
            config: Bot configuration dictionary (contains all .env variables)
                    Access like: config['position_size_usdc'], config['check_interval_seconds']
            candle_store: Optional CandleStore instance for accessing historical OHLC data
                         Use this to fetch candles: candle_store.get_candles('1m', limit=1000)

        Example initialization:
            self.price_history = []  # Store recent prices
            self.buy_threshold = 140.0  # Buy when price drops below this
            self.sell_threshold = 145.0  # Sell when price rises above this
            self.rsi_period = 14  # RSI calculation period
        """
        super().__init__(config)

        # Store candle store reference if provided
        self.candle_store = candle_store

        # Initialize your strategy-specific state here
        # Examples:
        # self.price_history = []
        # self.moving_average_short = None
        # self.moving_average_long = None
        # self.indicators = {}

        logger.info("SkeletonStrategy initialized")
        logger.warning(
            "This is a skeleton strategy that does nothing. "
            "Implement your own buy/sell logic or it will never trade."
        )

    def update(self, current_price: float) -> None:
        """
        Update strategy state with new price data.

        Called BEFORE should_buy() or should_sell() on every iteration.
        Use this to:
        - Store price history: self.price_history.append(current_price)
        - Calculate indicators: self.rsi = calculate_rsi(self.price_history)
        - Update moving averages, signals, etc.

        Args:
            current_price: Current SOL/USDC price (e.g., 142.35)

        Example implementation:
            # Store recent prices (keep last 100)
            self.price_history.append(current_price)
            if len(self.price_history) > 100:
                self.price_history.pop(0)

            # Calculate simple moving average
            if len(self.price_history) >= 20:
                self.sma_20 = sum(self.price_history[-20:]) / 20

        Example with OHLC data:
            if self.candle_store:
                # Get last 200 1-minute candles
                candles = self.candle_store.get_candles('1m', limit=200)

                # Calculate RSI
                closes = [c.close for c in candles.candles]
                self.rsi = self.calculate_rsi(closes, period=14)

                # Calculate MACD
                self.macd = self.calculate_macd(closes)
        """
        # Your update logic here
        # Example: self.price_history.append(current_price)

        logger.debug(f"Price updated: ${current_price:.4f}")

    def should_buy(self, current_price: float) -> bool:
        """
        Determine if a BUY signal should be generated.

        This is ONLY called when position == FLAT (no current position).
        Return True to enter a LONG position (buy SOL with USDC).

        The bot will:
        1. Check you have sufficient USDC balance
        2. Execute swap via Jupiter (USDC → SOL)
        3. Call self.on_buy(entry_price) to update position tracking
        4. Start calling should_sell() on subsequent iterations

        Args:
            current_price: Current SOL/USDC price (e.g., 142.35)

        Returns:
            True to trigger a buy, False to wait

        Example implementations:

        Simple price threshold:
            return current_price < 140.0  # Buy when SOL drops below $140

        With entry price tracking:
            if self.entry_price and current_price < self.entry_price * 0.95:
                return True  # Buy if price drops 5% from last sell
            return False

        RSI oversold:
            if self.rsi < 30:  # RSI below 30 = oversold
                return True
            return False

        Moving average crossover:
            if self.sma_short > self.sma_long:  # Golden cross
                return True
            return False

        Combined indicators:
            if self.rsi < 40 and self.macd > 0 and current_price > self.sma_20:
                return True
            return False
        """
        # Your buy logic here
        # Example: return current_price < 140.0

        return False  # Default: never buy

    def should_sell(self, current_price: float) -> bool:
        """
        Determine if a SELL signal should be generated.

        This is ONLY called when position == LONG (currently holding SOL).
        Return True to exit the position (sell SOL for USDC).

        The bot will:
        1. Check you have SOL balance
        2. Execute swap via Jupiter (SOL → USDC)
        3. Call self.on_sell(exit_price) to update position tracking
        4. Calculate P&L automatically
        5. Start calling should_buy() on subsequent iterations

        Args:
            current_price: Current SOL/USDC price (e.g., 145.50)

        Returns:
            True to trigger a sell, False to hold

        You have access to:
        - self.entry_price: Price you bought at (e.g., 142.35)
        - self.position: Always Position.LONG when this is called

        Example implementations:

        Fixed profit target (5%):
            if current_price >= self.entry_price * 1.05:
                return True  # Sell for 5% profit
            return False

        Fixed stop-loss (2%):
            if current_price <= self.entry_price * 0.98:
                return True  # Cut losses at 2%
            return False

        Profit target + stop-loss:
            profit_target = self.entry_price * 1.05  # 5% profit
            stop_loss = self.entry_price * 0.98      # 2% loss
            if current_price >= profit_target or current_price <= stop_loss:
                return True
            return False

        RSI overbought:
            if self.rsi > 70:  # RSI above 70 = overbought
                return True
            return False

        Trailing stop (protect profits):
            # Track highest price since entry
            if not hasattr(self, 'highest_price'):
                self.highest_price = current_price

            self.highest_price = max(self.highest_price, current_price)

            # Sell if price drops 3% from peak
            if current_price <= self.highest_price * 0.97:
                return True
            return False

        Time-based exit (hold for max 4 hours):
            import time
            if not hasattr(self, 'entry_time'):
                self.entry_time = time.time()

            hours_held = (time.time() - self.entry_time) / 3600
            if hours_held >= 4:
                return True  # Exit after 4 hours regardless of price

            # Also check profit target
            if current_price >= self.entry_price * 1.03:
                return True
            return False
        """
        # Your sell logic here
        # Example: return current_price > self.entry_price * 1.05  # 5% profit

        return False  # Default: never sell

    # HELPER METHODS (optional - add your own as needed)

    def calculate_rsi(self, prices: list[float], period: int = 14) -> float:
        """
        Example helper: Calculate RSI (Relative Strength Index).

        RSI ranges from 0-100:
        - RSI < 30: Oversold (potential buy signal)
        - RSI > 70: Overbought (potential sell signal)

        Args:
            prices: List of closing prices
            period: RSI period (typically 14)

        Returns:
            RSI value (0-100)
        """
        if len(prices) < period + 1:
            return 50.0  # Neutral if not enough data

        # Calculate price changes
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]

        # Separate gains and losses
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]

        # Calculate average gain and loss
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_sma(self, prices: list[float], period: int) -> float:
        """
        Example helper: Calculate Simple Moving Average.

        Args:
            prices: List of closing prices
            period: Number of periods to average

        Returns:
            SMA value
        """
        if len(prices) < period:
            return prices[-1] if prices else 0.0

        return sum(prices[-period:]) / period

    def calculate_ema(self, prices: list[float], period: int) -> float:
        """
        Example helper: Calculate Exponential Moving Average.

        EMA gives more weight to recent prices.

        Args:
            prices: List of closing prices
            period: Number of periods

        Returns:
            EMA value
        """
        if len(prices) < period:
            return prices[-1] if prices else 0.0

        multiplier = 2 / (period + 1)
        ema = prices[0]

        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema

        return ema
