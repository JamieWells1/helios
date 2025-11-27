"""
Wallet management for the trading bot.
"""

import base58
from typing import Optional

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from spl.token.instructions import get_associated_token_address

from .client import SolanaClient
from ..utils.logging import get_logger

logger = get_logger(__name__)


class Wallet:
    """
    Manages wallet operations including keypair loading and balance queries.
    """

    def __init__(self, wallet_private_key: str, rpc_client: SolanaClient):
        """
        Initialize wallet with private key and RPC client.

        Args:
            wallet_private_key: Base58 encoded private key
            rpc_client: Solana RPC client instance
        """
        self.rpc_client = rpc_client
        self.keypair: Optional[Keypair] = None
        self.pubkey: Optional[Pubkey] = None

        logger.info("Initializing wallet...")
        self._load_keypair(wallet_private_key)

    def _load_keypair(self, wallet_private_key: str) -> None:
        """
        Load keypair from base58 encoded private key.

        Args:
            wallet_private_key: Base58 encoded private key string
        """
        try:
            decoded = base58.b58decode(wallet_private_key)

            self.keypair = Keypair.from_bytes(decoded)
            self.pubkey = self.keypair.pubkey()

            logger.info(f"Wallet loaded successfully. Public key: {self.pubkey}")

        except Exception as e:
            logger.error(f"Failed to load wallet keypair: {e}")
            raise ValueError(f"Invalid private key: {e}")

    def get_sol_balance(self) -> Optional[float]:
        """
        Get SOL balance for this wallet.

        Returns:
            Balance in SOL, or None if query fails
        """
        if not self.pubkey:
            logger.error("Wallet not initialized")
            return None

        balance = self.rpc_client.get_balance(self.pubkey)
        if balance is not None:
            logger.info(f"SOL Balance: {balance:.4f} SOL")
        return balance

    def get_token_balance(self, token_mint: str) -> Optional[float]:
        """
        Get SPL token balance for this wallet.

        Args:
            token_mint: Token mint address as string

        Returns:
            Token balance, or None if query fails
        """
        if not self.pubkey:
            logger.error("Wallet not initialized")
            return None

        try:
            mint_pubkey = Pubkey.from_string(token_mint)
            token_account = get_associated_token_address(self.pubkey, mint_pubkey)

            balance = self.rpc_client.get_token_balance(token_account)
            if balance is not None:
                logger.info(f"Token Balance ({token_mint[:8]}...): {balance:.4f}")
            return balance

        except Exception as e:
            logger.error(f"Failed to get token balance for {token_mint}: {e}")
            return None

    def get_usdc_balance(self, usdc_mint: str) -> Optional[float]:
        """
        Get USDC balance for this wallet.

        Args:
            usdc_mint: USDC token mint address

        Returns:
            USDC balance, or None if query fails
        """
        return self.get_token_balance(usdc_mint)

    def validate_balance(
        self, required_usdc: float, usdc_mint: str, buffer_percent: float = 5.0
    ) -> bool:
        """
        Validate that wallet has sufficient USDC balance for a trade.

        Args:
            required_usdc: Required USDC amount
            usdc_mint: USDC token mint address
            buffer_percent: Additional buffer percentage (for fees)

        Returns:
            True if sufficient balance exists, False otherwise
        """
        current_balance = self.get_usdc_balance(usdc_mint)

        if current_balance is None:
            logger.error("Could not retrieve USDC balance")
            return False

        required_with_buffer = required_usdc * (1 + buffer_percent / 100)

        if current_balance < required_with_buffer:
            logger.warning(
                f"Insufficient USDC balance. "
                f"Required: {required_with_buffer:.2f}, "
                f"Available: {current_balance:.2f}"
            )
            return False

        logger.info(
            f"Balance validation passed. "
            f"Required: {required_with_buffer:.2f}, "
            f"Available: {current_balance:.2f}"
        )
        return True
