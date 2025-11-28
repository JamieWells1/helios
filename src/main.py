"""
Main entry point for the Solana trading bot.
"""

import os
import sys
import time
import signal
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

from src.blockchain.client import SolanaClient
from src.blockchain.wallet import Wallet
from src.blockchain.trader import JupiterTrader
from src.data.price_feed import PriceFeed
from src.data.candle_store import CandleStore, StoreConfig
from src.strategies.base import BaseStrategy, Signal
from src.strategies.skeleton import SkeletonStrategy
from src.strategies.registry import StrategyRegistry, register_strategy
from src.utils.logging import setup_logging, get_logger
from src.utils.state import StateManager


shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger = get_logger(__name__)
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True


class TradingBot:
    """
    Main trading bot orchestrator.
    """

    def __init__(self):
        """Initialize the trading bot."""
        self.logger = get_logger(__name__)
        self.config = self._load_config()

        self.state_manager = StateManager()
        self.rpc_client: Optional[SolanaClient] = None
        self.wallet: Optional[Wallet] = None
        self.trader: Optional[JupiterTrader] = None
        self.price_feed: Optional[PriceFeed] = None
        self.candle_store: Optional[CandleStore] = None
        self.strategy: Optional[BaseStrategy] = None
        self.use_ohlc_data: bool = False

    def _load_config(self) -> dict:
        """
        Load and validate configuration from environment variables.

        Returns:
            Configuration dictionary

        Raises:
            ValueError: If required configuration is missing or invalid
        """
        load_dotenv()

        config = {
            # RPC and wallet
            'rpc_url': os.getenv('SOLANA_RPC_URL'),
            'wallet_private_key': os.getenv('WALLET_PRIVATE_KEY'),

            # Trading pair
            'sol_mint': os.getenv('SOL_MINT', 'So11111111111111111111111111111111111111112'),
            'usdc_mint': os.getenv('USDC_MINT', 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'),

            # Position sizing
            'position_size_usdc': float(os.getenv('POSITION_SIZE_USDC', '100')),
            'max_position_size_usdc': float(os.getenv('MAX_POSITION_SIZE_USDC', '1000')),

            # Trading parameters
            'max_slippage_percent': float(os.getenv('MAX_SLIPPAGE_PERCENT', '1.0')),
            'check_interval_seconds': int(os.getenv('CHECK_INTERVAL_SECONDS', '10')),

            # API configuration
            'max_retries': int(os.getenv('MAX_RETRIES', '3')),
            'retry_delay_seconds': float(os.getenv('RETRY_DELAY_SECONDS', '1')),
            'max_retry_delay_seconds': float(os.getenv('MAX_RETRY_DELAY_SECONDS', '60')),

            # Price feed
            'use_coingecko': os.getenv('USE_COINGECKO', 'true').lower() == 'true',
            'use_jupiter': os.getenv('USE_JUPITER', 'true').lower() == 'true',
            'price_cache_seconds': int(os.getenv('PRICE_CACHE_SECONDS', '5')),

            # Logging
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'max_log_size_bytes': int(os.getenv('MAX_LOG_SIZE_BYTES', '10485760')),
            'log_backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5')),

            # OHLC data (optional, for advanced strategies)
            'use_ohlc_data': os.getenv('USE_OHLC_DATA', 'false').lower() == 'true',
            'ohlc_timeframe': os.getenv('OHLC_TIMEFRAME', '1h'),
            'ohlc_history_limit': int(os.getenv('OHLC_HISTORY_LIMIT', '200')),
        }

        # Validate required fields
        if not config['rpc_url']:
            raise ValueError("SOLANA_RPC_URL is required")
        if not config['wallet_private_key']:
            raise ValueError("WALLET_PRIVATE_KEY is required")

        self.logger.info("Configuration loaded successfully")
        self.logger.info(f"Position size: ${config['position_size_usdc']} USDC")
        self.logger.info(f"Check interval: {config['check_interval_seconds']}s")

        return config

    def initialize(self, strategy: Optional[BaseStrategy] = None) -> None:
        """
        Initialize all bot components.

        Args:
            strategy: Optional strategy instance to use. If None, uses SkeletonStrategy.
        """
        self.logger.info("Initializing trading bot components...")

        self.rpc_client = SolanaClient(
            rpc_url=self.config['rpc_url'],
            max_retries=self.config['max_retries'],
            retry_delay=self.config['retry_delay_seconds']
        )

        self.wallet = Wallet(
            wallet_private_key=self.config['wallet_private_key'],
            rpc_client=self.rpc_client
        )

        self.trader = JupiterTrader(
            rpc_client=self.rpc_client,
            keypair=self.wallet.keypair,
            max_retries=self.config['max_retries'],
            retry_delay=self.config['retry_delay_seconds']
        )

        self.price_feed = PriceFeed(
            use_coingecko=self.config['use_coingecko'],
            use_jupiter=self.config['use_jupiter'],
            cache_seconds=self.config['price_cache_seconds'],
            max_retries=self.config['max_retries'],
            retry_delay=self.config['retry_delay_seconds']
        )

        # Initialize OHLC data store if enabled
        self.use_ohlc_data = self.config['use_ohlc_data']
        if self.use_ohlc_data:
            self.logger.info("Initializing OHLC data store...")
            store_config = StoreConfig(
                db_path="data/candles.db",
                auto_discover_pool=True
            )
            self.candle_store = CandleStore(store_config)

            # Backfill historical data
            timeframe = self.config['ohlc_timeframe']
            limit = self.config['ohlc_history_limit']
            self.logger.info(f"Backfilling {limit} {timeframe} candles...")
            self.candle_store.backfill(timeframe, limit)

        # Use provided strategy or create skeleton
        if strategy:
            self.strategy = strategy
            self.logger.info(f"Using provided strategy: {strategy.__class__.__name__}")
        else:
            self.strategy = SkeletonStrategy(self.config)
            self.logger.warning(
                "No strategy provided - using SkeletonStrategy (does nothing). "
                "Implement your own strategy and pass it to bot.initialize()"
            )

        self._load_state()

        self.logger.info("All components initialized successfully")

    def _load_state(self) -> None:
        """Load bot state from persistence."""
        state = self.state_manager.load_state()

        if self.strategy and state:
            self.strategy.load_state(state)

    def _save_state(self) -> None:
        """Save bot state to persistence."""
        if self.strategy:
            state = self.strategy.get_state()
            self.state_manager.save_state(state)

    def run(self) -> None:
        """
        Main trading loop.

        Continuously fetches prices, evaluates strategy, and executes trades.
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting trading bot main loop")
        self.logger.info("=" * 60)

        iteration = 0

        while not shutdown_requested:
            try:
                iteration += 1
                self.logger.info(f"\n--- Iteration {iteration} [{datetime.utcnow().isoformat()}] ---")

                if not self.rpc_client.check_health():
                    self.logger.warning("RPC unhealthy, attempting reconnection...")
                    if not self.rpc_client.reconnect():
                        self.logger.error("Reconnection failed, waiting before retry...")
                        time.sleep(30)
                        continue

                # Update OHLC data if enabled
                if self.use_ohlc_data and self.candle_store:
                    timeframe = self.config['ohlc_timeframe']
                    self.candle_store.update_latest(timeframe)

                current_price = self.price_feed.get_sol_price()
                if current_price is None:
                    self.logger.error("Failed to fetch price, skipping iteration")
                    time.sleep(self.config['check_interval_seconds'])
                    continue

                sol_balance = self.wallet.get_sol_balance()
                usdc_balance = self.wallet.get_usdc_balance(self.config['usdc_mint'])

                if sol_balance is None or usdc_balance is None:
                    self.logger.error("Failed to fetch balances, skipping iteration")
                    time.sleep(self.config['check_interval_seconds'])
                    continue

                # Get signal from strategy (supports both OHLC and price-based strategies)
                signal = self._get_strategy_signal(current_price)

                if signal == Signal.BUY:
                    self._execute_buy(current_price, usdc_balance)
                elif signal == Signal.SELL:
                    self._execute_sell(current_price, sol_balance)
                else:
                    self.logger.info("No action (HOLD)")

                self._save_state()

                time.sleep(self.config['check_interval_seconds'])

            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
                self.logger.info("Continuing operation after error...")
                time.sleep(self.config['check_interval_seconds'])

        self.logger.info("Trading bot main loop stopped")
        self._shutdown()

    def _get_strategy_signal(self, current_price: float) -> Signal:
        """
        Get trading signal from strategy.

        Supports both OHLC-based and price-based strategies.

        Args:
            current_price: Current market price

        Returns:
            Trading signal (BUY, SELL, or HOLD)
        """
        # Check if strategy supports OHLC data
        if (self.use_ohlc_data and
            self.candle_store and
            hasattr(self.strategy, 'should_buy_candles')):

            # Get candle data
            timeframe = self.config['ohlc_timeframe']
            limit = self.config['ohlc_history_limit']
            candles = self.candle_store.get_candles(timeframe, limit)

            # Update strategy with current price
            self.strategy.update(current_price)

            # Check for buy/sell signals using candles
            if self.strategy.position.value == 'flat':
                if self.strategy.should_buy_candles(candles):
                    self.logger.info(f"BUY signal generated at price ${current_price:.4f}")
                    return Signal.BUY
            elif self.strategy.position.value == 'long':
                if self.strategy.should_sell_candles(candles):
                    self.logger.info(f"SELL signal generated at price ${current_price:.4f}")
                    return Signal.SELL

            return Signal.HOLD

        # Fall back to legacy price-based signal
        return self.strategy.get_signal(current_price)

    def _execute_buy(self, current_price: float, usdc_balance: float) -> None:
        """
        Execute a buy order.

        Args:
            current_price: Current market price
            usdc_balance: Available USDC balance
        """
        self.logger.info("Executing BUY order...")

        position_size = self.strategy.get_position_size(usdc_balance)

        if not self.wallet.validate_balance(position_size, self.config['usdc_mint']):
            self.logger.error("Insufficient balance for buy order")
            return

        signature = self.trader.buy_sol_with_usdc(
            usdc_amount=position_size,
            usdc_mint=self.config['usdc_mint'],
            sol_mint=self.config['sol_mint'],
            max_slippage_percent=self.config['max_slippage_percent']
        )

        if signature:
            self.logger.info(f"BUY order executed successfully: {signature}")
            self.strategy.on_buy(current_price)
            self._save_state()
        else:
            self.logger.error("BUY order failed")

    def _execute_sell(self, current_price: float, sol_balance: float) -> None:
        """
        Execute a sell order.

        Args:
            current_price: Current market price
            sol_balance: Available SOL balance
        """
        self.logger.info("Executing SELL order...")

        position_size_usdc = self.strategy.get_position_size(0)
        sol_amount = position_size_usdc / current_price

        if sol_amount > sol_balance:
            self.logger.warning(
                f"Not enough SOL to sell. Required: {sol_amount:.4f}, "
                f"Available: {sol_balance:.4f}"
            )

        signature = self.trader.sell_sol_for_usdc(
            sol_amount=sol_amount,
            sol_mint=self.config['sol_mint'],
            usdc_mint=self.config['usdc_mint'],
            max_slippage_percent=self.config['max_slippage_percent']
        )

        if signature:
            self.logger.info(f"SELL order executed successfully: {signature}")
            self.strategy.on_sell(current_price)
            self._save_state()
        else:
            self.logger.error("SELL order failed")

    def _shutdown(self) -> None:
        """Gracefully shutdown the bot."""
        self.logger.info("Shutting down trading bot...")

        self._save_state()

        self.logger.info("Shutdown complete")


def main():
    """Main entry point."""
    logger = setup_logging(
        log_level=os.getenv('LOG_LEVEL', 'INFO'),
        max_bytes=int(os.getenv('MAX_LOG_SIZE_BYTES', '10485760')),
        backup_count=int(os.getenv('LOG_BACKUP_COUNT', '5'))
    )

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("=" * 60)
    logger.info("Solana Trading Bot Starting...")
    logger.info("=" * 60)

    try:
        bot = TradingBot()
        bot.initialize()

        bot.run()

    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
