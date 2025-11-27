"""
Strategy registry for managing available strategies.

Use this to register your custom strategies and make them available to the bot.
"""

from typing import Dict, Type, Any
from .base import BaseStrategy
from ..utils.logging import get_logger

logger = get_logger(__name__)


class StrategyRegistry:
    """
    Registry for managing trading strategies.

    Register your strategies here to make them available to the bot.
    """

    _strategies: Dict[str, Type[BaseStrategy]] = {}

    @classmethod
    def register(cls, name: str, strategy_class: Type[BaseStrategy]) -> None:
        """
        Register a strategy.

        Args:
            name: Name to register the strategy under
            strategy_class: The strategy class to register
        """
        cls._strategies[name] = strategy_class
        logger.info(f"Registered strategy: {name}")

    @classmethod
    def get(cls, name: str) -> Type[BaseStrategy]:
        """
        Get a registered strategy class.

        Args:
            name: Name of the strategy

        Returns:
            Strategy class

        Raises:
            ValueError: If strategy not found
        """
        if name not in cls._strategies:
            available = ', '.join(cls._strategies.keys()) or 'none'
            raise ValueError(
                f"Strategy '{name}' not found. Available strategies: {available}"
            )
        return cls._strategies[name]

    @classmethod
    def create(cls, name: str, config: Dict[str, Any]) -> BaseStrategy:
        """
        Create an instance of a registered strategy.

        Args:
            name: Name of the strategy
            config: Configuration dictionary

        Returns:
            Strategy instance
        """
        strategy_class = cls.get(name)
        return strategy_class(config)

    @classmethod
    def list_strategies(cls) -> list[str]:
        """
        Get list of registered strategy names.

        Returns:
            List of strategy names
        """
        return list(cls._strategies.keys())


# Helper decorator for easy strategy registration
def register_strategy(name: str):
    """
    Decorator to register a strategy.

    Usage:
        @register_strategy('my_strategy')
        class MyStrategy(BaseStrategy):
            ...
    """
    def decorator(strategy_class: Type[BaseStrategy]):
        StrategyRegistry.register(name, strategy_class)
        return strategy_class
    return decorator
