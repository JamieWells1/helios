"""
Integration tests for trading functionality.

Tests actual buy and sell operations with small amounts.
"""

import unittest
import os
import time
import logging
from dotenv import load_dotenv

from src.blockchain.client import SolanaClient
from src.blockchain.wallet import Wallet
from src.blockchain.trader import JupiterTrader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)


class TestTrading(unittest.TestCase):
    """Test actual trading operations."""

    @classmethod
    def setUpClass(cls):
        """Set up trading components once for all tests."""
        logger.info("=" * 70)
        logger.info("SETTING UP TRADING TESTS")
        logger.info("=" * 70)

        load_dotenv()

        # Check required environment variables
        rpc_url = os.getenv('SOLANA_RPC_URL')
        private_key = os.getenv('WALLET_PRIVATE_KEY')

        if not rpc_url or not private_key:
            raise ValueError(
                "Missing required environment variables: "
                "SOLANA_RPC_URL and WALLET_PRIVATE_KEY must be set"
            )

        # Initialize components
        logger.info("Initializing Solana client...")
        cls.rpc_client = SolanaClient(rpc_url=rpc_url)

        logger.info("Initializing wallet...")
        cls.wallet = Wallet(
            wallet_private_key=private_key,
            rpc_client=cls.rpc_client
        )

        logger.info("Initializing Jupiter trader...")
        cls.trader = JupiterTrader(
            rpc_client=cls.rpc_client,
            keypair=cls.wallet.keypair
        )

        # Token mints
        cls.sol_mint = os.getenv('SOL_MINT', 'So11111111111111111111111111111111111111112')
        cls.usdc_mint = os.getenv('USDC_MINT', 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')

        # Test amount (0.1 SOL worth of USDC)
        cls.test_sol_amount = 0.1

        logger.info(f"SOL mint: {cls.sol_mint}")
        logger.info(f"USDC mint: {cls.usdc_mint}")
        logger.info(f"Test amount: {cls.test_sol_amount} SOL")
        logger.info("=" * 70)

    def setUp(self):
        """Log test start."""
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"STARTING TEST: {self._testMethodName}")
        logger.info("=" * 70)

    def tearDown(self):
        """Log test completion."""
        logger.info("=" * 70)
        logger.info(f"COMPLETED TEST: {self._testMethodName}")
        logger.info("=" * 70)
        logger.info("")

    def test_1_check_balances(self):
        """Test 0: Check initial balances before trading."""
        logger.info("Checking wallet balances...")

        sol_balance = self.wallet.get_sol_balance()
        usdc_balance = self.wallet.get_usdc_balance(self.usdc_mint)

        self.assertIsNotNone(sol_balance, "Failed to get SOL balance")
        self.assertIsNotNone(usdc_balance, "Failed to get USDC balance")

        logger.info(f"✓ SOL Balance: {sol_balance:.4f} SOL")
        logger.info(f"✓ USDC Balance: {usdc_balance:.2f} USDC")

        # Verify sufficient balances for testing
        min_usdc_needed = 20  # Minimum USDC needed for 0.1 SOL purchase

        if usdc_balance < min_usdc_needed:
            self.skipTest(
                f"Insufficient USDC balance for testing. "
                f"Need at least {min_usdc_needed} USDC, have {usdc_balance:.2f}"
            )

        logger.info(f"✓ Sufficient balances for testing")

    def test_2_buy_sol(self):
        """Test 1: Buy 0.1 SOL with USDC."""
        logger.info("=" * 70)
        logger.info("TEST 1: BUY 0.1 SOL WITH USDC")
        logger.info("=" * 70)

        # Get initial balances
        initial_sol = self.wallet.get_sol_balance()
        initial_usdc = self.wallet.get_usdc_balance(self.usdc_mint)

        logger.info(f"Initial SOL balance: {initial_sol:.4f} SOL")
        logger.info(f"Initial USDC balance: {initial_usdc:.2f} USDC")

        # Estimate USDC needed (rough estimate: 0.1 SOL * $200/SOL = $20)
        # We'll use a fixed amount for the test
        usdc_amount = 20.0  # $20 USDC

        logger.info(f"Attempting to buy ~{self.test_sol_amount} SOL with {usdc_amount} USDC...")

        # Execute buy
        signature = self.trader.buy_sol_with_usdc(
            usdc_amount=usdc_amount,
            usdc_mint=self.usdc_mint,
            sol_mint=self.sol_mint,
            max_slippage_percent=1.0
        )

        self.assertIsNotNone(signature, "Buy order failed - no signature returned")

        logger.info(f"✓ BUY ORDER SUCCESSFUL")
        logger.info(f"✓ Transaction signature: {signature}")
        logger.info(f"✓ View on Solscan: https://solscan.io/tx/{signature}")

        # Wait for transaction to confirm on blockchain
        confirmed = self.rpc_client.confirm_transaction(signature, max_wait_seconds=30)
        if not confirmed:
            logger.warning("Transaction did not confirm within timeout, but may still succeed")

        # Additional brief wait to ensure balance propagation
        time.sleep(2)

        # Check final balances
        final_sol = self.wallet.get_sol_balance()
        final_usdc = self.wallet.get_usdc_balance(self.usdc_mint)

        sol_gained = final_sol - initial_sol
        usdc_spent = initial_usdc - final_usdc

        logger.info("")
        logger.info("TRADE RESULTS:")
        logger.info(f"  SOL gained: +{sol_gained:.4f} SOL")
        logger.info(f"  USDC spent: -{usdc_spent:.2f} USDC")
        logger.info(f"  Final SOL balance: {final_sol:.4f} SOL")
        logger.info(f"  Final USDC balance: {final_usdc:.2f} USDC")

        # Verify we gained SOL
        self.assertGreater(sol_gained, 0, "SOL balance should have increased")
        self.assertGreater(usdc_spent, 0, "USDC balance should have decreased")

    def test_3_sell_sol(self):
        """Test 2: Sell 0.1 SOL for USDC."""
        logger.info("=" * 70)
        logger.info("TEST 2: SELL 0.1 SOL FOR USDC")
        logger.info("=" * 70)

        # Get initial balances
        initial_sol = self.wallet.get_sol_balance()
        initial_usdc = self.wallet.get_usdc_balance(self.usdc_mint)

        logger.info(f"Initial SOL balance: {initial_sol:.4f} SOL")
        logger.info(f"Initial USDC balance: {initial_usdc:.2f} USDC")

        # Check if we have enough SOL
        if initial_sol < self.test_sol_amount:
            self.skipTest(
                f"Insufficient SOL balance. "
                f"Need {self.test_sol_amount}, have {initial_sol:.4f}"
            )

        logger.info(f"Attempting to sell {self.test_sol_amount} SOL for USDC...")

        # Execute sell
        signature = self.trader.sell_sol_for_usdc(
            sol_amount=self.test_sol_amount,
            sol_mint=self.sol_mint,
            usdc_mint=self.usdc_mint,
            max_slippage_percent=1.0
        )

        self.assertIsNotNone(signature, "Sell order failed - no signature returned")

        logger.info(f"✓ SELL ORDER SUCCESSFUL")
        logger.info(f"✓ Transaction signature: {signature}")
        logger.info(f"✓ View on Solscan: https://solscan.io/tx/{signature}")

        # Wait for transaction to confirm on blockchain
        confirmed = self.rpc_client.confirm_transaction(signature, max_wait_seconds=30)
        if not confirmed:
            logger.warning("Transaction did not confirm within timeout, but may still succeed")

        # Additional brief wait to ensure balance propagation
        time.sleep(2)

        # Check final balances
        final_sol = self.wallet.get_sol_balance()
        final_usdc = self.wallet.get_usdc_balance(self.usdc_mint)

        sol_sold = initial_sol - final_sol
        usdc_gained = final_usdc - initial_usdc

        logger.info("")
        logger.info("TRADE RESULTS:")
        logger.info(f"  SOL sold: -{sol_sold:.4f} SOL")
        logger.info(f"  USDC gained: +{usdc_gained:.2f} USDC")
        logger.info(f"  Final SOL balance: {final_sol:.4f} SOL")
        logger.info(f"  Final USDC balance: {final_usdc:.2f} USDC")

        # Verify we sold SOL and gained USDC
        self.assertGreater(sol_sold, 0, "SOL balance should have decreased")
        self.assertGreater(usdc_gained, 0, "USDC balance should have increased")

        # Verify we sold approximately the right amount (with some tolerance for fees)
        self.assertAlmostEqual(
            sol_sold, self.test_sol_amount,
            delta=0.01,  # Allow 0.01 SOL difference for fees
            msg=f"Should have sold ~{self.test_sol_amount} SOL"
        )

    @classmethod
    def tearDownClass(cls):
        """Final cleanup and summary."""
        logger.info("")
        logger.info("=" * 70)
        logger.info("ALL TRADING TESTS COMPLETED")
        logger.info("=" * 70)
        logger.info("")


if __name__ == "__main__":
    unittest.main(verbosity=2)
