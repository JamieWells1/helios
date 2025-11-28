# Strategy Implementation Guide

## Quick Start

Implementing a custom trading strategy is simple:

1. **Copy the skeleton**: `cp src/strategies/skeleton.py src/strategies/my_strategy.py`
2. **Rename the class**: Change `SkeletonStrategy` to `MyStrategy`
3. **Implement logic**: Fill in `update()`, `should_buy()`, and `should_sell()`
4. **Run your bot**: See example below

## Minimal Example

```python
# run_bot.py
from src.main import TradingBot
from src.strategies.my_strategy import MyStrategy

# Create bot
bot = TradingBot()

# Create your strategy
strategy = MyStrategy(bot.config)

# Initialize with your strategy
bot.initialize(strategy=strategy)

# Run
bot.run()
```

For complete examples and API reference, see src/strategies/skeleton.py which contains extensive documentation and example implementations.
