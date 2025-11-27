"""
State persistence for the trading bot.

Handles saving and loading bot state to/from JSON files using atomic writes.
"""

import json
import os
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .logging import get_logger

logger = get_logger(__name__)


class StateManager:
    """
    Manages persistent state for the trading bot.

    Handles saving current position, entry prices, timestamps, and strategy state
    using atomic file writes to prevent corruption.
    """

    def __init__(self, state_dir: str = "data", state_file: str = "bot_state.json"):
        """
        Initialize state manager.

        Args:
            state_dir: Directory to store state files
            state_file: Name of the state file
        """
        self.state_dir = Path(state_dir)
        self.state_file = self.state_dir / state_file
        self.state: Dict[str, Any] = {}

        self.state_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"State manager initialized with file: {self.state_file}")

    def load_state(self) -> Dict[str, Any]:
        """
        Load state from disk.

        Returns:
            Dictionary containing saved state, or empty dict if no state exists
        """
        if not self.state_file.exists():
            logger.info("No existing state file found, starting with empty state")
            self.state = self._get_default_state()
            return self.state

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                self.state = json.load(f)
            logger.info(
                f"State loaded successfully: {self._sanitize_state_for_log(self.state)}"
            )
            return self.state
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load state file: {e}")
            logger.warning("Starting with default state")
            self.state = self._get_default_state()
            return self.state

    def save_state(self, state: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save state to disk using atomic write.

        Args:
            state: State dictionary to save, or None to save current state

        Returns:
            True if save was successful, False otherwise
        """
        if state is not None:
            self.state = state

        self.state["last_updated"] = datetime.utcnow().isoformat()

        try:
            temp_fd, temp_path = tempfile.mkstemp(
                dir=self.state_dir, prefix=".tmp_state_", suffix=".json", text=True
            )

            try:
                with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                    json.dump(self.state, f, indent=2, ensure_ascii=False)

                shutil.move(temp_path, self.state_file)
                logger.debug(
                    f"State saved successfully: {self._sanitize_state_for_log(self.state)}"
                )
                return True

            except Exception as e:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                raise e

        except (IOError, OSError) as e:
            logger.error(f"Failed to save state: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the state.

        Args:
            key: State key to retrieve
            default: Default value if key doesn't exist

        Returns:
            Value from state or default
        """
        return self.state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the state.

        Args:
            key: State key to set
            value: Value to store
        """
        self.state[key] = value

    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple state values at once.

        Args:
            updates: Dictionary of key-value pairs to update
        """
        self.state.update(updates)

    def _get_default_state(self) -> Dict[str, Any]:
        """
        Get default empty state structure.

        Returns:
            Default state dictionary
        """
        return {
            "position": "flat",  # 'flat', 'long', or 'short'
            "entry_price": None,
            "entry_time": None,
            "entry_amount_usdc": None,
            "last_updated": datetime.utcnow().isoformat(),
            "strategy_state": {},
        }

    def _sanitize_state_for_log(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a sanitized copy of state for logging (remove sensitive data).

        Args:
            state: Original state dictionary

        Returns:
            Sanitized state dictionary safe for logging
        """
        return {k: v for k, v in state.items() if k != "wallet_private_key"}
