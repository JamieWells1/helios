# Backtesting Guide

Test your trading strategy on historical data without risking real funds.

## Quick Start

### Option 1: Command Line

```bash
# Run with custom strategy (edit src/main.py to set your strategy)
python3 src/main.py --test

# Specify number of candles to backtest
python3 src/main.py --test --candles 5000
```

### Option 2: Custom Script

```python
# run_backtest.py
from src.main import TradingBot
from src.strategies.custom_strategy import MeanReversionStrategy

bot = TradingBot()
bot.initialize(backtest_mode=True)
strategy = MeanReversionStrategy(bot.config, candle_store=bot.candle_store)
bot.strategy = strategy
bot.backtest(num_candles=10000)
```

Then run:
```bash
python3 run_backtest.py
```

## How It Works

1. **Loads Historical Data**: Fetches the last N candles from the database (fetches any missing ones automatically)
2. **Simulates Trading**: Iterates through each candle, calling your strategy's `update()`, `should_buy()`, and `should_sell()` methods
3. **Tracks P&L**: Simulates orders with a virtual $10,000 USDC balance
4. **Runs Fast**: No blockchain calls, no live data - just pure simulation
5. **Logs Everything**: Shows every buy/sell with price, P&L, and hold duration

## Example Output

```
============================================================
BACKTEST MODE
============================================================
Backtesting on last 10000 candles
Loaded 10000 candles
Period: 2025-11-21 05:30:00 to 2025-11-28 12:15:00
============================================================
Starting balance: $10000.00 USDC
Position size: $100.00 per trade

[1523/10000] BUY  @ $142.3500 | Size: $100.00 | Cash: $9900.00
[1687/10000] SELL @ $144.8200 | P&L: +$1.73 (+1.73%) | Hold: 0:02:44 | Cash: $10001.73
[2341/10000] BUY  @ $141.2000 | Size: $100.00 | Cash: $9901.73
[2456/10000] SELL @ $143.5000 | P&L: +$1.63 (+1.63%) | Hold: 0:01:55 | Cash: $10003.36

============================================================
BACKTEST RESULTS
============================================================
Total trades: 24
Starting balance: $10,000.00
Ending balance: $10,087.45
Total P&L: +$87.45 (+0.87%)
Winning trades: 18/24 (75.0%)
Average win: $6.92
Average loss: -$3.41
Best trade: +$12.34 (+12.34%)
Worst trade: -$8.21 (-8.21%)
============================================================
```

## Configuration

Backtest respects your `.env` settings:

- `POSITION_SIZE_USDC`: Size of each trade
- `OHLC_STARTUP_TIMEFRAME`: Candle timeframe (usually 1m)
- `OHLC_STARTUP_LIMIT`: Max candles available

## What Data Is Used?

- **Source**: Local SQLite database (`data/candles.db`)
- **Timeframe**: 1-minute candles (configurable)
- **Amount**: Last 10,000 candles by default (~7 days)
- **Auto-fetch**: Missing candles are fetched automatically from GeckoTerminal

## Benefits

✓ **No Risk**: No real money involved
✓ **Fast**: Runs through 10,000 candles in seconds
✓ **Accurate**: Uses actual historical price data
✓ **Iterative**: Test, tweak strategy, test again
✓ **Decoupled**: No wallet, RPC, or blockchain needed

## Tips

1. **Start Small**: Test on 1,000 candles first (`--candles 1000`)
2. **Multiple Runs**: Run backtest multiple times after tweaking parameters
3. **Different Periods**: Test on different time periods by fetching fresh data
4. **Log Analysis**: Review logs to understand strategy behavior
5. **Win Rate**: Aim for >60% win rate with good risk/reward ratio

## Limitations

- **No Slippage**: Assumes you get exact prices (real trading has slippage)
- **No Fees**: Doesn't account for DEX fees (~0.3%)
- **Perfect Execution**: Assumes all orders fill instantly
- **Historical Data Only**: Past performance ≠ future results

## Next Steps

After backtesting:
1. Adjust strategy parameters based on results
2. Test on different time periods
3. When satisfied, run with small real position size
4. Monitor live performance vs backtest
