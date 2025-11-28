# Strategy System

This directory contains the strategy framework for the trading bot.

## Files

- **base.py**: Abstract base class that all strategies must inherit from
- **skeleton.py**: Template with extensive documentation and examples

## Quick Start

### 1. Copy the Skeleton

```bash
cp src/strategies/skeleton.py src/strategies/my_strategy.py
```

### 2. Rename and Implement

Open `my_strategy.py` and:
- Rename `SkeletonStrategy` to `MyStrategy`
- Implement `update()`, `should_buy()`, and `should_sell()`

The skeleton file contains detailed documentation with examples.

### 3. Run Your Strategy

```python
# run_bot.py
from src.main import TradingBot
from src.strategies.my_strategy import MyStrategy

bot = TradingBot()
strategy = MyStrategy(bot.config)
bot.initialize(strategy=strategy)
bot.run()
```

## Strategy Interface

All strategies must implement three methods:

### `update(current_price: float) -> None`

Called every iteration before signals are checked.

**Use for:** Updating indicators, storing price history, calculating metrics

```python
def update(self, current_price: float) -> None:
    self.price_history.append(current_price)
    self.rsi = self.calculate_rsi(self.price_history)
```

### `should_buy(current_price: float) -> bool`

Called only when position is FLAT (no holdings).

**Return:** `True` to buy, `False` to wait

```python
def should_buy(self, current_price: float) -> bool:
    return self.rsi < 30  # Buy when oversold
```

### `should_sell(current_price: float) -> bool`

Called only when position is LONG (holding SOL).

**Return:** `True` to sell, `False` to hold

```python
def should_sell(self, current_price: float) -> bool:
    profit = (current_price / self.entry_price - 1) * 100
    return profit >= 5.0  # Sell at 5% profit
```

## Available Data

Your strategy has access to:

- `self.config`: Bot configuration dictionary (all .env variables)
- `self.position`: Current position (Position.FLAT or Position.LONG)
- `self.entry_price`: Price when position was entered (if LONG, else None)
- `self.strategy_state`: Dictionary for storing custom state
- `self.candle_store`: Historical OHLC data (if USE_OHLC_DATA=true and passed to __init__)

## Accessing OHLC Data

If `USE_OHLC_DATA=true` in `.env`:

```python
def __init__(self, config, candle_store=None):
    super().__init__(config)
    self.candle_store = candle_store

def update(self, current_price: float) -> None:
    if self.candle_store:
        candles = self.candle_store.get_candles('1m', limit=1000)
        closes = [c.close for c in candles.candles]
        self.rsi = self.calculate_rsi(closes, period=14)
```

## Lifecycle Hooks

Optional methods you can override:

- `on_buy(price)`: Called after successful buy execution
- `on_sell(price)`: Called after successful sell execution (calculates P&L automatically)
- `get_state()`: Return state dictionary for persistence
- `load_state(state)`: Restore state from persistence

## More Information

See `src/strategies/skeleton.py` for:
- Detailed API documentation
- Multiple example implementations
- Helper methods for calculating RSI, SMA, EMA
- Common patterns (trailing stops, time-based exits, etc.)
