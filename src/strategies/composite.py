"""
Strategy composition for chaining multiple strategies together.
"""

from typing import Dict, Any, List
from enum import Enum

from .base import BaseStrategy
from ..utils.logging import get_logger

logger = get_logger(__name__)


class CompositeMode(Enum):
    """How to combine signals from multiple strategies."""
    ALL = "all"  # All strategies must agree (AND logic)
    ANY = "any"  # Any strategy can trigger (OR logic)
    MAJORITY = "majority"  # Majority vote wins
    WEIGHTED = "weighted"  # Weighted voting based on strategy priority


class CompositeStrategy(BaseStrategy):
    """
    Combines multiple strategies using configurable logic.

    Allows you to chain strategies together and combine their signals.
    Useful for building complex strategies from simple components.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        strategies: List[BaseStrategy],
        mode: CompositeMode = CompositeMode.ALL,
        weights: List[float] = None
    ):
        """
        Initialize composite strategy.

        Args:
            config: Configuration dictionary
            strategies: List of strategy instances to combine
            mode: How to combine signals (ALL, ANY, MAJORITY, WEIGHTED)
            weights: Optional weights for WEIGHTED mode (must sum to 1.0)
        """
        super().__init__(config)

        if not strategies:
            raise ValueError("CompositeStrategy requires at least one strategy")

        self.strategies = strategies
        self.mode = mode
        self.weights = weights

        # Validate weights for weighted mode
        if mode == CompositeMode.WEIGHTED:
            if not weights or len(weights) != len(strategies):
                raise ValueError(
                    "WEIGHTED mode requires weights list matching strategies length"
                )
            if abs(sum(weights) - 1.0) > 0.001:
                raise ValueError("Weights must sum to 1.0")

        logger.info(
            f"CompositeStrategy initialized with {len(strategies)} strategies "
            f"using {mode.value} mode"
        )

    def update(self, current_price: float) -> None:
        """
        Update all child strategies with new price data.

        Args:
            current_price: Current market price
        """
        for strategy in self.strategies:
            strategy.update(current_price)

    def should_buy(self, current_price: float) -> bool:
        """
        Determine buy signal by combining child strategy signals.

        Args:
            current_price: Current market price

        Returns:
            True if combined signal indicates buy, False otherwise
        """
        signals = [strategy.should_buy(current_price) for strategy in self.strategies]

        if self.mode == CompositeMode.ALL:
            # All strategies must agree
            result = all(signals)
            logger.debug(f"Buy signals (ALL): {signals} -> {result}")
            return result

        elif self.mode == CompositeMode.ANY:
            # Any strategy can trigger
            result = any(signals)
            logger.debug(f"Buy signals (ANY): {signals} -> {result}")
            return result

        elif self.mode == CompositeMode.MAJORITY:
            # Majority vote
            yes_votes = sum(signals)
            result = yes_votes > len(signals) / 2
            logger.debug(f"Buy signals (MAJORITY): {yes_votes}/{len(signals)} -> {result}")
            return result

        elif self.mode == CompositeMode.WEIGHTED:
            # Weighted voting
            score = sum(
                weight if signal else 0
                for signal, weight in zip(signals, self.weights)
            )
            result = score > 0.5
            logger.debug(f"Buy signals (WEIGHTED): score={score:.2f} -> {result}")
            return result

        return False

    def should_sell(self, current_price: float) -> bool:
        """
        Determine sell signal by combining child strategy signals.

        Args:
            current_price: Current market price

        Returns:
            True if combined signal indicates sell, False otherwise
        """
        signals = [strategy.should_sell(current_price) for strategy in self.strategies]

        if self.mode == CompositeMode.ALL:
            result = all(signals)
            logger.debug(f"Sell signals (ALL): {signals} -> {result}")
            return result

        elif self.mode == CompositeMode.ANY:
            result = any(signals)
            logger.debug(f"Sell signals (ANY): {signals} -> {result}")
            return result

        elif self.mode == CompositeMode.MAJORITY:
            yes_votes = sum(signals)
            result = yes_votes > len(signals) / 2
            logger.debug(f"Sell signals (MAJORITY): {yes_votes}/{len(signals)} -> {result}")
            return result

        elif self.mode == CompositeMode.WEIGHTED:
            score = sum(
                weight if signal else 0
                for signal, weight in zip(signals, self.weights)
            )
            result = score > 0.5
            logger.debug(f"Sell signals (WEIGHTED): score={score:.2f} -> {result}")
            return result

        return False

    def on_buy(self, entry_price: float) -> None:
        """
        Notify all child strategies of buy execution.

        Args:
            entry_price: Price at which position was entered
        """
        super().on_buy(entry_price)
        for strategy in self.strategies:
            strategy.on_buy(entry_price)

    def on_sell(self, exit_price: float) -> None:
        """
        Notify all child strategies of sell execution.

        Args:
            exit_price: Price at which position was exited
        """
        super().on_sell(exit_price)
        for strategy in self.strategies:
            strategy.on_sell(exit_price)

    def get_state(self) -> Dict[str, Any]:
        """
        Get state for all child strategies.

        Returns:
            Dictionary containing composite state
        """
        return {
            'position': self.position.value,
            'entry_price': self.entry_price,
            'strategy_states': [s.get_state() for s in self.strategies]
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        """
        Load state for all child strategies.

        Args:
            state: Dictionary containing saved state
        """
        super().load_state(state)

        strategy_states = state.get('strategy_states', [])
        for strategy, strategy_state in zip(self.strategies, strategy_states):
            strategy.load_state(strategy_state)
