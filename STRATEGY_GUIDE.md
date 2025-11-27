# Strategy Implementation Guide

This guide shows you how to implement and run custom trading strategies with the bot.

## Overview

The bot now uses a **flexible strategy system** where:
- Strategy logic lives in Python code (not .env config)
- You can chain multiple strategies together
- Strategies are composable and reusable

## Quick Start

### 1. Implement Your Strategy

Create a new Python file (e.g., `my_strategy.py`):

```python
from src.strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    """Your custom trading strategy."""

    def __init__(self, config):
        super().__init__(config)
        # Initialize your state here
        self.prices = []

    def update(self, current_price: float) -> None:
        """Called every iteration - update your indicators here."""
        self.prices.append(current_price)

    def should_buy(self, current_price: float) -> bool:
        """Return True when you want to buy."""
        # Your buy logic here
        return len(self.prices) > 5 and current_price < sum(self.prices[-5:]) / 5

    def should_sell(self, current_price: float) -> bool:
        """Return True when you want to sell."""
        # Your sell logic here
        if not self.entry_price:
            return False
        return current_price > self.entry_price * 1.05  # 5% profit
```

### 2. Run the Bot with Your Strategy

Create a runner script (e.g., `run_my_bot.py`):

```python
from src.main import TradingBot
from my_strategy import MyStrategy

# Create bot
bot = TradingBot()

# Create your strategy
strategy = MyStrategy(bot.config)

# Initialize with your strategy
bot.initialize(strategy=strategy)

# Run
bot.run()
```

### 3. Execute

```bash
python run_my_bot.py
```

## Strategy Chaining

Combine multiple strategies for more complex logic:

```python
from src.main import TradingBot
from src.strategies.composite import CompositeStrategy, CompositeMode
from my_strategies import StrategyA, StrategyB, StrategyC

bot = TradingBot()

# Create individual strategies
strat_a = StrategyA(bot.config)
strat_b = StrategyB(bot.config)
strat_c = StrategyC(bot.config)

# Combine: ALL must agree to buy
composite = CompositeStrategy(
    config=bot.config,
    strategies=[strat_a, strat_b, strat_c],
    mode=CompositeMode.ALL  # All strategies must agree
)

bot.initialize(strategy=composite)
bot.run()
```

### Composite Modes

Choose how to combine strategy signals:

**ALL** - All strategies must agree (AND logic)
```python
mode=CompositeMode.ALL
```

**ANY** - Any strategy can trigger (OR logic)
```python
mode=CompositeMode.ANY
```

**MAJORITY** - Majority vote wins
```python
mode=CompositeMode.MAJORITY
```

**WEIGHTED** - Weighted voting
```python
mode=CompositeMode.WEIGHTED
weights=[0.5, 0.3, 0.2]  # Must sum to 1.0
```

## What You Have Access To

Inside your strategy:

### Configuration
```python
self.config['position_size_usdc']  # Position size
self.config['max_slippage_percent']  # Slippage tolerance
# All config from .env is available
```

### Position State
```python
self.position  # Position.FLAT or Position.LONG
self.entry_price  # Price when position entered (if LONG)
```

### Custom State
```python
self.strategy_state = {'key': 'value'}  # Persisted across restarts
```

## Lifecycle Hooks

Your strategy will receive these callbacks:

```python
def update(self, current_price: float) -> None:
    """Called every iteration before checking signals."""
    pass

def should_buy(self, current_price: float) -> bool:
    """Called only when FLAT. Return True to enter."""
    return False

def should_sell(self, current_price: float) -> bool:
    """Called only when LONG. Return True to exit."""
    return False

def on_buy(self, entry_price: float) -> None:
    """Called after successful buy execution."""
    pass

def on_sell(self, exit_price: float) -> None:
    """Called after successful sell execution."""
    pass

def get_state(self) -> dict:
    """Return state to persist to disk."""
    return super().get_state()

def load_state(self, state: dict) -> None:
    """Restore state from disk."""
    super().load_state(state)
```

## Examples

See `example_strategies.py` for:
- Simple threshold strategy
- Moving average strategy
- Profit target strategy
- Composite strategy examples
- Weighted voting examples

## Templates

Use the skeleton template:
```bash
cp src/strategies/skeleton.py my_strategy.py
# Edit my_strategy.py
```

## Tips

1. **Start Simple**: Begin with basic logic, test thoroughly
2. **Use Logging**: Import logger and log your decisions
   ```python
   from ..utils.logging import get_logger
   logger = get_logger(__name__)
   logger.info(f"Price crossed threshold: {price}")
   ```
3. **Test on Devnet**: Always test with fake money first
4. **State Persistence**: Use `self.strategy_state` for data you want to survive restarts
5. **Composition**: Break complex strategies into simple components and chain them

## Advanced: Different Buy/Sell Logic

For strategies that need different logic for entry vs exit:

```python
from src.strategies.composite import CompositeStrategy, CompositeMode

# Strategy optimized for entries
entry_strategy = MyEntryStrategy(config)

# Strategy optimized for exits
exit_strategy = MyExitStrategy(config)

# Custom composite that uses different logic for buy/sell
class CustomComposite(CompositeStrategy):
    def should_buy(self, price):
        return entry_strategy.should_buy(price)

    def should_sell(self, price):
        return exit_strategy.should_sell(price)

bot.initialize(strategy=CustomComposite(config, [entry_strategy, exit_strategy]))
```

## No .env Config Needed

The old system required strategy parameters in `.env`:
```bash
# OLD - Don't do this
STRATEGY_NAME=MovingAverageCrossover
MA_SHORT_PERIOD=5
MA_LONG_PERIOD=20
```

New system - everything in code:
```python
# NEW - Do this
class MyMA(BaseStrategy):
    def __init__(self, config, short=5, long=20):
        super().__init__(config)
        self.short = short
        self.long = long
```

This gives you:
- Type safety
- IDE autocomplete
- No string parsing
- Version control for strategy params
- Easy to test different parameter combinations
