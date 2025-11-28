import unittest
from datetime import datetime
from pathlib import Path
import sqlite3
import logging

from src.data.candle_store import CandleStore, StoreConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestCandleStore(unittest.TestCase):
    def setUp(self):
        """Set up an in-memory SQLite database for testing."""
        self.db_path = Path(":memory:")
        self.config = StoreConfig(db_path=str(self.db_path), pool_address="test_pool")

        # Use a shared SQLite connection for the in-memory database
        self.connection = sqlite3.connect(":memory:")

        # Create the CandleStore with the shared connection
        # The _init_database method will be called automatically
        self.store = CandleStore(self.config, connection=self.connection)

        # Pre-populate the database with test data
        cursor = self.connection.cursor()
        # Use Unix timestamp (integer) as per the schema
        test_timestamp = int(datetime(2025, 11, 28, 19, 41, 0).timestamp())
        cursor.execute(
            """
            INSERT INTO candles (timeframe, timestamp, open, high, low, close, volume)
            VALUES ('1m', ?, 1.0, 2.0, 0.5, 1.5, 100.0)
            """,
            (test_timestamp,)
        )
        self.connection.commit()
        self.test_timestamp = test_timestamp

    def test_get_last_candle_time(self):
        """Test that _get_last_candle_time returns the correct timestamp."""
        test_timeframe = "1m"

        # Call the method
        last_candle_time = self.store._get_last_candle_time(test_timeframe)

        # Assert the result (should return integer timestamp)
        self.assertEqual(last_candle_time, self.test_timestamp)

    def tearDown(self):
        """Clean up the in-memory database."""
        self.connection.close()


if __name__ == "__main__":
    unittest.main()
