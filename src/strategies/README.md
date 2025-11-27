# Strategy System

This directory contains the strategy framework for the trading bot.

## Files

- **base.py**: Abstract base class that all strategies must inherit from
- **skeleton.py**: Template for creating new strategies
- **composite.py**: System for chaining multiple strategies together
- **registry.py**: Strategy registration system (optional, for advanced use)

## Quick Start

### 1. Create Your Strategy

Copy `skeleton.py` or create a new file:

```python
from src.strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        # Initialize your state

    def update(self, current_price: float) -> None:
        # Update indicators, store price history, etc.
        pass

    def should_buy(self, current_price: float) -> bool:
        # Return True when you want to enter a position
        return False

    def should_sell(self, current_price: float) -> bool:
        # Return True when you want to exit a position
        return False
```

### 2. Use Your Strategy

In your main script:

```python
from src.main import TradingBot
from my_strategy import MyStrategy

bot = TradingBot()
strategy = MyStrategy(bot.config)
bot.initialize(strategy=strategy)
bot.run()
```

## Strategy Chaining

Combine multiple strategies using `CompositeStrategy`:

```python
from src.strategies.composite import CompositeStrategy, CompositeMode

# Create multiple strategies
strategy1 = MyStrategy1(config)
strategy2 = MyStrategy2(config)

# Combine with AND logic (all must agree)
composite = CompositeStrategy(
    config=config,
    strategies=[strategy1, strategy2],
    mode=CompositeMode.ALL
)

bot.initialize(strategy=composite)
```

### Composite Modes

- **ALL**: All strategies must agree (AND logic)
- **ANY**: Any strategy can trigger (OR logic)
- **MAJORITY**: Majority vote wins
- **WEIGHTED**: Weighted voting (provide weights list)

## Available Context

Your strategy has access to:

- `self.config`: Configuration dictionary from the bot
- `self.position`: Current position (Position.FLAT or Position.LONG)
- `self.entry_price`: Price when position was entered (if LONG)
- `self.strategy_state`: Dictionary for storing custom state

## Lifecycle Methods

- `update(price)`: Called every iteration before signals are checked
- `should_buy(price)`: Called only when FLAT, return True to buy
- `should_sell(price)`: Called only when LONG, return True to sell
- `on_buy(price)`: Called after successful buy execution
- `on_sell(price)`: Called after successful sell execution
- `get_state()`: Return state dictionary for persistence
- `load_state(state)`: Restore state from persistence

## Examples

See `example_strategies.py` in the project root for complete examples.
