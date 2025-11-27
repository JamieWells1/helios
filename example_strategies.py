"""
Example of how to implement and use custom strategies.

This file shows:
1. How to create a simple custom strategy
2. How to chain multiple strategies together
3. How to run the bot with your strategy
"""

from src.main import TradingBot
from src.strategies.base import BaseStrategy
from src.strategies.skeleton import SkeletonStrategy
from src.strategies.composite import CompositeStrategy, CompositeMode


# Example 1: Simple custom strategy
class SimpleThresholdStrategy(BaseStrategy):
    """
    Buy when price drops below a threshold, sell when it rises above another.
    """

    def __init__(self, config):
        super().__init__(config)
        self.buy_threshold = 100.0  # Buy when SOL < $100
        self.sell_threshold = 110.0  # Sell when SOL > $110

    def update(self, current_price: float) -> None:
        """No state to update for this simple strategy."""
        pass

    def should_buy(self, current_price: float) -> bool:
        """Buy when price drops below threshold."""
        return current_price < self.buy_threshold

    def should_sell(self, current_price: float) -> bool:
        """Sell when price rises above threshold."""
        return current_price > self.sell_threshold


# Example 2: Moving average strategy
class SimpleMovingAverageStrategy(BaseStrategy):
    """
    Track price history and buy/sell based on moving average.
    """

    def __init__(self, config, period=10):
        super().__init__(config)
        self.period = period
        self.prices = []

    def update(self, current_price: float) -> None:
        """Store price history."""
        self.prices.append(current_price)
        if len(self.prices) > self.period:
            self.prices.pop(0)

    def should_buy(self, current_price: float) -> bool:
        """Buy when price is below moving average."""
        if len(self.prices) < self.period:
            return False
        ma = sum(self.prices) / len(self.prices)
        return current_price < ma * 0.98  # 2% below MA

    def should_sell(self, current_price: float) -> bool:
        """Sell when price is above moving average."""
        if len(self.prices) < self.period:
            return False
        ma = sum(self.prices) / len(self.prices)
        return current_price > ma * 1.02  # 2% above MA


# Example 3: Profit target strategy
class ProfitTargetStrategy(BaseStrategy):
    """
    Sell when profit target is reached.
    """

    def __init__(self, config, profit_target_percent=5.0):
        super().__init__(config)
        self.profit_target_percent = profit_target_percent

    def update(self, current_price: float) -> None:
        """No state to update."""
        pass

    def should_buy(self, current_price: float) -> bool:
        """Always ready to buy (delegate to other strategies)."""
        return True

    def should_sell(self, current_price: float) -> bool:
        """Sell when profit target is reached."""
        if not self.entry_price:
            return False

        profit_percent = ((current_price - self.entry_price) / self.entry_price) * 100
        return profit_percent >= self.profit_target_percent


def example_simple_strategy():
    """Run bot with a simple threshold strategy."""
    bot = TradingBot()

    # Create your custom strategy
    strategy = SimpleThresholdStrategy(bot.config)

    # Initialize bot with your strategy
    bot.initialize(strategy=strategy)

    # Run the bot
    bot.run()


def example_composite_strategy():
    """Run bot with multiple strategies combined."""
    bot = TradingBot()

    # Create individual strategies
    threshold = SimpleThresholdStrategy(bot.config)
    ma_strategy = SimpleMovingAverageStrategy(bot.config, period=10)
    profit_target = ProfitTargetStrategy(bot.config, profit_target_percent=5.0)

    # Combine them: ALL strategies must agree on buy,
    # ANY strategy can trigger sell
    composite = CompositeStrategy(
        config=bot.config,
        strategies=[threshold, ma_strategy],
        mode=CompositeMode.ALL  # Both must agree to buy
    )

    # For sells, create another composite with ANY mode
    # This is just an example - you can structure this however you want
    bot.initialize(strategy=composite)
    bot.run()


def example_weighted_strategy():
    """Run bot with weighted voting between strategies."""
    bot = TradingBot()

    # Create strategies
    strategy1 = SimpleThresholdStrategy(bot.config)
    strategy2 = SimpleMovingAverageStrategy(bot.config, period=10)
    strategy3 = ProfitTargetStrategy(bot.config)

    # Use weighted voting: strategy1 has 50% vote, others have 25% each
    composite = CompositeStrategy(
        config=bot.config,
        strategies=[strategy1, strategy2, strategy3],
        mode=CompositeMode.WEIGHTED,
        weights=[0.5, 0.25, 0.25]
    )

    bot.initialize(strategy=composite)
    bot.run()


if __name__ == '__main__':
    # Run one of the examples:

    # Simple single strategy
    # example_simple_strategy()

    # Multiple strategies combined
    # example_composite_strategy()

    # Weighted combination
    # example_weighted_strategy()

    # Or implement your own strategy inline:
    bot = TradingBot()

    # Quick inline strategy
    class MyStrategy(BaseStrategy):
        def update(self, current_price: float) -> None:
            pass

        def should_buy(self, current_price: float) -> bool:
            # Your buy logic here
            return False

        def should_sell(self, current_price: float) -> bool:
            # Your sell logic here
            return False

    bot.initialize(strategy=MyStrategy(bot.config))
    bot.run()
