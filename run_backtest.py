"""
Run backtest with custom strategy.

Usage:
    python3 run_backtest.py

This will simulate trading on the last 10,000 1-minute candles (~7 days).
No real trades are executed - it's purely for testing strategy performance.
"""

from src.main import TradingBot
from src.strategies.custom_strategy import MeanReversionStrategy


def main():
    """Run backtest with mean reversion strategy."""
    # Create bot
    bot = TradingBot()

    # Initialize in backtest mode (no wallet/blockchain needed)
    bot.initialize(backtest_mode=True)

    # Create strategy with candle store access
    strategy = MeanReversionStrategy(bot.config, candle_store=bot.candle_store)

    # Set the strategy
    bot.strategy = strategy

    # Run backtest on last 10,000 candles
    bot.backtest(num_candles=10000)


if __name__ == "__main__":
    main()
