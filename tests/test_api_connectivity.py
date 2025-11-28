import unittest
from src.blockchain.client import SolanaClient
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TestAPIConnectivity(unittest.TestCase):

    def setUp(self):
        logger.info("Setting up SolanaClient for API connectivity tests.")
        self.client = SolanaClient("https://api.mainnet-beta.solana.com")

    def test_health_check(self):
        logger.info("Running health check test.")
        self.assertTrue(self.client.check_health(), "RPC health check failed")
        logger.info("Health check test passed.")

    def test_reconnect(self):
        logger.info("Running reconnect test.")
        self.assertTrue(self.client.reconnect(), "Failed to reconnect to RPC endpoint")
        logger.info("Reconnect test passed.")


if __name__ == "__main__":
    unittest.main()
