"""
Example: Running the bot with RSI strategy using OHLC data.

This demonstrates how to use the RSI strategy with real OHLC candle data.
"""

from src.main import TradingBot
from src.strategies.rsi_strategy import RSIStrategy, RSIStrategyConfig
from src.utils.logging import setup_logging, get_logger


def main():
    """
    Run the trading bot with RSI strategy.

    Before running:
    1. Set environment variables in .env file
    2. Set USE_OHLC_DATA=true to enable OHLC data fetching
    3. Optional: Adjust RSI parameters below
    """

    logger = setup_logging(log_level='INFO')
    logger.info("=" * 60)
    logger.info("Starting RSI Trading Bot")
    logger.info("=" * 60)

    logger.info("Step 1: Initializing TradingBot...")
    bot = TradingBot()
    logger.info("✓ TradingBot instance created")

    logger.info("Step 2: Configuring RSI strategy...")
    strategy_config = RSIStrategyConfig(
        rsi_oversold=30.0,
        rsi_overbought=70.0,
        rsi_period=14,
        min_candles_required=50
    )
    logger.info(f"✓ RSI config: oversold={strategy_config.rsi_oversold}, overbought={strategy_config.rsi_overbought}")

    logger.info("Step 3: Creating RSI strategy instance...")
    strategy = RSIStrategy(
        config=bot.config,
        strategy_config=strategy_config
    )
    logger.info("✓ RSI strategy created")

    logger.info("Step 4: Initializing bot components...")
    logger.info("This may take a minute if fetching OHLC data for the first time...")
    bot.initialize(strategy=strategy)
    logger.info("✓ Bot initialized successfully")

    logger.info("Step 5: Starting main trading loop...")
    bot.run()


if __name__ == '__main__':
    main()
