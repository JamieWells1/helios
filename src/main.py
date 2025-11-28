"""
Main entry point for the Solana trading bot.
"""

import os
import sys
import time
import signal
import argparse
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

from src.blockchain.client import SolanaClient
from src.blockchain.wallet import Wallet
from src.blockchain.trader import JupiterTrader
from src.data.price_feed import PriceFeed
from src.data.candle_store import CandleStore, StoreConfig
from src.data.data_aggregator import DataAggregator, DataAggregatorConfig
from src.data.sources.base import DataSourceConfig, DataSourceType, DataSourcePurpose
from src.data.sources.cryptocompare import CryptoCompareSource
from src.data.sources.geckoterminal import GeckoTerminalSource
from src.strategies.base import BaseStrategy, Signal
from src.strategies.skeleton import SkeletonStrategy
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
        self.data_aggregator: Optional[DataAggregator] = None
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
            'ohlc_startup_timeframe': os.getenv('OHLC_STARTUP_TIMEFRAME', '1m'),
            'ohlc_startup_limit': int(os.getenv('OHLC_STARTUP_LIMIT', '10000')),
            'ohlc_runtime_timeframe': os.getenv('OHLC_RUNTIME_TIMEFRAME', '1m'),
            'ohlc_runtime_limit': int(os.getenv('OHLC_RUNTIME_LIMIT', '5')),

            # Data source API URLs
            'cryptocompare_base_url': os.getenv('CRYPTOCOMPARE_BASE_URL', 'https://min-api.cryptocompare.com/data/v2'),
            'cryptocompare_api_key': os.getenv('CRYPTOCOMPARE_API_KEY', None),
            'geckoterminal_base_url': os.getenv('GECKOTERMINAL_BASE_URL', 'https://api.geckoterminal.com/api/v2'),
            'jupiter_quote_api': os.getenv('JUPITER_QUOTE_API', 'https://quote-api.jup.ag/v6/quote'),
            'jupiter_swap_api': os.getenv('JUPITER_SWAP_API', 'https://quote-api.jup.ag/v6/swap'),
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

    def initialize(self, strategy: Optional[BaseStrategy] = None, backtest_mode: bool = False) -> None:
        """
        Initialize all bot components.

        Args:
            strategy: Optional strategy instance to use. If None, uses SkeletonStrategy.
            backtest_mode: If True, skip wallet/blockchain initialization (for backtesting only)
        """
        self.logger.info("Initializing trading bot components...")

        if not backtest_mode:
            # Only initialize wallet/blockchain components for live trading
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
                jupiter_quote_api=self.config['jupiter_quote_api'],
                jupiter_swap_api=self.config['jupiter_swap_api'],
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
        else:
            self.logger.info("Backtest mode: Skipping wallet/blockchain initialization")

        # Initialize OHLC data system if enabled
        self.use_ohlc_data = self.config['use_ohlc_data']
        if self.use_ohlc_data:
            self.logger.info("Initializing multi-source data aggregator...")

            # Create CryptoCompare source for startup historical data
            cryptocompare_config = DataSourceConfig(
                source_type=DataSourceType.CRYPTOCOMPARE,
                purpose=DataSourcePurpose.HISTORICAL,
                base_url=self.config['cryptocompare_base_url'],
                api_key=self.config.get('cryptocompare_api_key'),
                max_retries=self.config['max_retries'],
                retry_delay=self.config['retry_delay_seconds']
            )
            cryptocompare_source = CryptoCompareSource(cryptocompare_config)

            # Create GeckoTerminal source for runtime price updates
            geckoterminal_config = DataSourceConfig(
                source_type=DataSourceType.GECKOTERMINAL,
                purpose=DataSourcePurpose.RUNTIME,
                base_url=self.config['geckoterminal_base_url'],
                max_retries=self.config['max_retries'],
                retry_delay=self.config['retry_delay_seconds']
            )
            geckoterminal_source = GeckoTerminalSource(geckoterminal_config)

            # Create data aggregator with both sources
            aggregator_config = DataAggregatorConfig(
                historical_source=cryptocompare_source,
                runtime_source=geckoterminal_source,
                fallback_source=geckoterminal_source  # GeckoTerminal as fallback
            )
            self.data_aggregator = DataAggregator(aggregator_config)

            # Initialize candle store
            store_config = StoreConfig(
                db_path="data/candles.db",
                pool_address=geckoterminal_source.pool_address
            )
            self.candle_store = CandleStore(store_config)

            # Smart catch-up: Only fetch candles we're missing
            startup_tf = self.config['ohlc_startup_timeframe']
            startup_limit = self.config['ohlc_startup_limit']

            # Check what data we already have
            catch_up_info = self.candle_store.get_catch_up_info(startup_tf, startup_limit)

            self.logger.info("=" * 60)
            self.logger.info("STARTUP DATA CHECK")
            self.logger.info("=" * 60)
            self.logger.info(f"Target: {startup_limit} {startup_tf} candles")
            self.logger.info(f"Existing: {catch_up_info['existing_count']} candles in database")

            if catch_up_info['latest_timestamp']:
                from datetime import datetime
                latest_dt = datetime.fromtimestamp(catch_up_info['latest_timestamp'])
                self.logger.info(f"Latest candle: {latest_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                self.logger.info(f"Minutes behind: {catch_up_info['minutes_behind']}")
                self.logger.info(f"Candles needed: {catch_up_info['candles_needed']}")

            if catch_up_info['should_full_fetch']:
                # More than 10,000 minutes behind (or no data) - do full fetch
                self.logger.info(
                    f"→ Performing FULL FETCH of {startup_limit} candles "
                    f"(this may take 30-60 seconds)..."
                )

                startup_candles = self.data_aggregator.fetch_startup_historical_data(
                    timeframe=startup_tf,
                    limit=startup_limit
                )

                if startup_candles:
                    self.logger.info(f"Saving {len(startup_candles)} candles to database...")
                    self.candle_store.bulk_insert(startup_tf, startup_candles.candles)
                    self.logger.info("✓ Full historical data loaded")
                else:
                    self.logger.error("✗ Failed to fetch startup data")

            elif catch_up_info['candles_needed'] > 0:
                # Only fetch the candles we're missing (catch-up)
                self.logger.info(
                    f"→ Performing CATCH-UP fetch of {catch_up_info['candles_needed']} candles "
                    f"(this will be quick)..."
                )

                catch_up_candles = self.data_aggregator.fetch_runtime_candles(
                    timeframe=startup_tf,
                    limit=catch_up_info['candles_needed']
                )

                if catch_up_candles:
                    self.logger.info(f"Saving {len(catch_up_candles)} new candles...")
                    self.candle_store.bulk_insert(startup_tf, catch_up_candles.candles)
                    self.logger.info(f"✓ Caught up with {len(catch_up_candles)} new candles")
                else:
                    self.logger.warning("⚠ Failed to fetch catch-up candles, using existing data")

            else:
                # Already up to date!
                self.logger.info("✓ Data is already up-to-date, no fetch needed")

            self.logger.info("=" * 60)

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
                        time.sleep(self.config['check_interval_seconds'])
                        continue

                # Update OHLC data if enabled
                # Fetch recent candles from runtime source (GeckoTerminal)
                if self.use_ohlc_data and self.data_aggregator:
                    runtime_tf = self.config['ohlc_runtime_timeframe']
                    runtime_limit = self.config['ohlc_runtime_limit']

                    recent_candles = self.data_aggregator.fetch_runtime_candles(
                        timeframe=runtime_tf,
                        limit=runtime_limit
                    )

                    if recent_candles and self.candle_store:
                        self.candle_store._save_to_db(runtime_tf, recent_candles.candles)

                # Get current price (from data aggregator if using OHLC, else from price_feed)
                if self.use_ohlc_data and self.data_aggregator:
                    current_price = self.data_aggregator.fetch_current_price()
                else:
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

    def backtest(self, num_candles: int = 10000) -> None:
        """
        Run backtest on historical data (no live trading).

        Simulates trading on the last num_candles to evaluate strategy performance.
        Runs fast - no blockchain calls, just signal generation and P&L tracking.

        Args:
            num_candles: Number of historical candles to backtest (default: 10000)
        """
        self.logger.info("=" * 60)
        self.logger.info("BACKTEST MODE")
        self.logger.info("=" * 60)
        self.logger.info(f"Backtesting on last {num_candles} candles")

        if not self.use_ohlc_data or not self.candle_store:
            self.logger.error("Backtest requires OHLC data (USE_OHLC_DATA=true in .env)")
            return

        # Ensure we have candles (fetch if needed)
        startup_tf = self.config['ohlc_startup_timeframe']
        catch_up_info = self.candle_store.get_catch_up_info(startup_tf, num_candles)

        if catch_up_info['candles_needed'] > 0:
            self.logger.info(f"Fetching {catch_up_info['candles_needed']} missing candles...")
            candles = self.data_aggregator.fetch_runtime_candles(
                timeframe=startup_tf,
                limit=catch_up_info['candles_needed']
            )
            if candles:
                self.candle_store.bulk_insert(startup_tf, candles.candles)
                self.logger.info("✓ Candles updated")

        # Load candles for backtest
        candle_list = self.candle_store.get_candles(startup_tf, limit=num_candles)

        if len(candle_list) < 100:
            self.logger.error(f"Not enough candles for backtest: {len(candle_list)}")
            return

        self.logger.info(f"Loaded {len(candle_list)} candles")
        self.logger.info(f"Period: {datetime.fromtimestamp(candle_list.candles[0].timestamp)} to {datetime.fromtimestamp(candle_list.candles[-1].timestamp)}")
        self.logger.info("=" * 60)

        # Backtest state
        position_size_usdc = self.config['position_size_usdc']
        cash = 10000.0  # Start with $10k USDC
        position = None  # None or {'entry_price': float, 'size_usdc': float}
        trades = []
        total_pnl = 0.0

        self.logger.info(f"Starting balance: ${cash:.2f} USDC")
        self.logger.info(f"Position size: ${position_size_usdc:.2f} per trade")
        self.logger.info("")

        # Iterate through candles
        for i, candle in enumerate(candle_list.candles):
            current_price = candle.close

            # Update strategy
            self.strategy.update(current_price)

            # Get signal
            signal = self.strategy.get_signal(current_price)

            # Execute based on signal
            if signal == Signal.BUY and position is None and cash >= position_size_usdc:
                # Simulate buy
                position = {
                    'entry_price': current_price,
                    'size_usdc': position_size_usdc,
                    'entry_time': datetime.fromtimestamp(candle.timestamp)
                }
                cash -= position_size_usdc
                self.strategy.on_buy(current_price)

                self.logger.info(f"[{i+1}/{len(candle_list)}] BUY  @ ${current_price:.4f} | Size: ${position_size_usdc:.2f} | Cash: ${cash:.2f}")

            elif signal == Signal.SELL and position is not None:
                # Simulate sell
                entry_price = position['entry_price']
                size_usdc = position['size_usdc']

                # Calculate P&L
                pnl_pct = ((current_price / entry_price) - 1) * 100
                pnl_usd = size_usdc * (pnl_pct / 100)

                cash += size_usdc + pnl_usd
                total_pnl += pnl_usd

                hold_duration = datetime.fromtimestamp(candle.timestamp) - position['entry_time']

                self.logger.info(
                    f"[{i+1}/{len(candle_list)}] SELL @ ${current_price:.4f} | "
                    f"P&L: ${pnl_usd:+.2f} ({pnl_pct:+.2f}%) | "
                    f"Hold: {hold_duration} | Cash: ${cash:.2f}"
                )

                trades.append({
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pnl_usd': pnl_usd,
                    'pnl_pct': pnl_pct,
                    'hold_duration': hold_duration
                })

                self.strategy.on_sell(current_price)
                position = None

        # Final summary
        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info("BACKTEST RESULTS")
        self.logger.info("=" * 60)
        self.logger.info(f"Total trades: {len(trades)}")
        self.logger.info(f"Starting balance: $10,000.00")
        self.logger.info(f"Ending balance: ${cash:.2f}")
        self.logger.info(f"Total P&L: ${total_pnl:+.2f} ({(total_pnl/10000)*100:+.2f}%)")

        if position:
            self.logger.info(f"Open position: Entry @ ${position['entry_price']:.4f} (unrealized)")

        if trades:
            winning_trades = [t for t in trades if t['pnl_usd'] > 0]
            losing_trades = [t for t in trades if t['pnl_usd'] <= 0]

            self.logger.info(f"Winning trades: {len(winning_trades)}/{len(trades)} ({len(winning_trades)/len(trades)*100:.1f}%)")

            if winning_trades:
                avg_win = sum(t['pnl_usd'] for t in winning_trades) / len(winning_trades)
                self.logger.info(f"Average win: ${avg_win:.2f}")

            if losing_trades:
                avg_loss = sum(t['pnl_usd'] for t in losing_trades) / len(losing_trades)
                self.logger.info(f"Average loss: ${avg_loss:.2f}")

            best_trade = max(trades, key=lambda t: t['pnl_usd'])
            worst_trade = min(trades, key=lambda t: t['pnl_usd'])

            self.logger.info(f"Best trade: ${best_trade['pnl_usd']:+.2f} ({best_trade['pnl_pct']:+.2f}%)")
            self.logger.info(f"Worst trade: ${worst_trade['pnl_usd']:+.2f} ({worst_trade['pnl_pct']:+.2f}%)")

        self.logger.info("=" * 60)

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

            # Get startup historical data (10,000 1m candles from CryptoCompare)
            startup_tf = self.config['ohlc_startup_timeframe']
            startup_limit = self.config['ohlc_startup_limit']

            # Get runtime recent data (5 1m candles from GeckoTerminal)
            runtime_tf = self.config['ohlc_runtime_timeframe']
            runtime_limit = self.config['ohlc_runtime_limit']

            # Fetch candles from database
            historical_candles = self.candle_store.get_candles(startup_tf, startup_limit)
            recent_candles = self.candle_store.get_candles(runtime_tf, runtime_limit)

            # Update strategy with current price
            self.strategy.update(current_price)

            # Pass historical candles to strategy (for indicators)
            # Strategy calculates RSI/MACD on large dataset
            if self.strategy.position.value == 'flat':
                if self.strategy.should_buy_candles(historical_candles):
                    self.logger.info(
                        f"BUY signal at ${current_price:.4f} "
                        f"(analyzed {len(historical_candles)} {startup_tf} candles)"
                    )
                    return Signal.BUY
            elif self.strategy.position.value == 'long':
                if self.strategy.should_sell_candles(historical_candles):
                    self.logger.info(
                        f"SELL signal at ${current_price:.4f} "
                        f"(analyzed {len(historical_candles)} {startup_tf} candles)"
                    )
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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Solana Trading Bot')
    parser.add_argument('--test', action='store_true', help='Run in backtest mode (simulated trading on historical data)')
    parser.add_argument('--candles', type=int, default=10000, help='Number of candles to backtest (default: 10000)')
    args = parser.parse_args()

    logger = setup_logging(
        log_level=os.getenv('LOG_LEVEL', 'INFO'),
        max_bytes=int(os.getenv('MAX_LOG_SIZE_BYTES', '10485760')),
        backup_count=int(os.getenv('LOG_BACKUP_COUNT', '5'))
    )

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("=" * 60)
    if args.test:
        logger.info("Solana Trading Bot - BACKTEST MODE")
    else:
        logger.info("Solana Trading Bot Starting...")
    logger.info("=" * 60)

    try:
        bot = TradingBot()

        if args.test:
            # Initialize in backtest mode (skips wallet/blockchain)
            bot.initialize(backtest_mode=True)
            # Run backtest mode (no live trading)
            bot.backtest(num_candles=args.candles)
        else:
            # Initialize for live trading
            bot.initialize(backtest_mode=False)
            # Run live trading mode
            bot.run()

    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
