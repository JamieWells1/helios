import unittest
from src.data.ohlc_fetcher import GeckoTerminalFetcher
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TestOHLCFetcher(unittest.TestCase):
    def setUp(self):
        logger.info("Setting up GeckoTerminalFetcher for OHLC tests.")
        self.fetcher = GeckoTerminalFetcher()

    def test_timeframe_mapping(self):
        logger.info("Running timeframe mapping test.")
        self.assertIn(
            "1m", self.fetcher.TIMEFRAME_MAP, "1m timeframe not found in mapping"
        )
        logger.info("1m timeframe found in mapping.")
        self.assertEqual(
            self.fetcher.TIMEFRAME_MAP["1m"].api_timeframe,
            "minute",
            "Incorrect API timeframe for 1m",
        )
        logger.info("Timeframe mapping test passed.")


if __name__ == "__main__":
    unittest.main()
