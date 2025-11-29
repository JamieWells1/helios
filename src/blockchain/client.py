"""
Solana RPC client with health checking and automatic reconnection.
"""

import time
from typing import Optional

from solana.rpc.api import Client
from solana.rpc.core import RPCException
from solders.pubkey import Pubkey
from solders.signature import Signature

from ..utils.logging import get_logger

logger = get_logger(__name__)


class SolanaClient:
    """
    Manages connection to Solana RPC endpoint with health checking.
    """

    def __init__(self, rpc_url: str, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize Solana RPC client.

        Args:
            rpc_url: URL of the Solana RPC endpoint
            max_retries: Maximum number of retry attempts for failed requests
            retry_delay: Initial delay between retries in seconds
        """
        self.rpc_url = rpc_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client: Optional[Client] = None

        logger.info(f"Initializing Solana RPC client with endpoint: {rpc_url}")
        self._connect()

    def _connect(self) -> None:
        """
        Establish connection to Solana RPC endpoint.
        """
        try:
            self.client = Client(self.rpc_url)
            version = self.client.get_version()
            logger.info(f"Connected to Solana RPC successfully. Version: {version.value}")
        except Exception as e:
            logger.error(f"Failed to connect to Solana RPC: {e}")
            raise

    def check_health(self) -> bool:
        """
        Check if the RPC connection is healthy.

        Returns:
            True if connection is healthy, False otherwise
        """
        if not self.client:
            logger.warning("Client not initialized")
            return False

        try:
            # Use get_version() instead of get_health() which doesn't exist
            response = self.client.get_version()
            logger.debug("RPC health check passed")
            return response.value is not None
        except Exception as e:
            logger.warning(f"RPC health check failed: {e}")
            return False

    def reconnect(self) -> bool:
        """
        Attempt to reconnect to the RPC endpoint.

        Returns:
            True if reconnection successful, False otherwise
        """
        logger.info("Attempting to reconnect to Solana RPC...")
        try:
            self._connect()
            return True
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            return False

    def get_balance(self, pubkey: Pubkey) -> Optional[float]:
        """
        Get SOL balance for a public key.

        Args:
            pubkey: Public key to query balance for

        Returns:
            Balance in SOL, or None if query fails
        """
        if not self.client:
            logger.error("Client not initialized")
            return None

        retries = 0
        delay = self.retry_delay

        while retries < self.max_retries:
            try:
                response = self.client.get_balance(pubkey)
                if response.value is not None:
                    balance_lamports = response.value
                    balance_sol = balance_lamports / 1e9  # Convert lamports to SOL
                    logger.debug(f"Balance for {pubkey}: {balance_sol} SOL")
                    return balance_sol
                else:
                    logger.warning(f"No balance data returned for {pubkey}")
                    return None
            except RPCException as e:
                retries += 1
                logger.warning(f"RPC error getting balance (attempt {retries}/{self.max_retries}): {e}")
                if retries < self.max_retries:
                    time.sleep(delay)
                    delay = min(delay * 2, 60)  # Exponential backoff, max 60s
            except Exception as e:
                logger.error(f"Unexpected error getting balance: {e}")
                return None

        logger.error(f"Failed to get balance after {self.max_retries} attempts")
        return None

    def get_token_balance(self, token_account: Pubkey) -> Optional[float]:
        """
        Get token balance for a token account.

        Args:
            token_account: Token account public key

        Returns:
            Token balance (0.0 if account doesn't exist), or None if query fails
        """
        if not self.client:
            logger.error("Client not initialized")
            return None

        retries = 0
        delay = self.retry_delay

        while retries < self.max_retries:
            try:
                response = self.client.get_token_account_balance(token_account)
                if response.value is not None:
                    balance = float(response.value.amount) / (10 ** response.value.decimals)
                    logger.debug(f"Token balance for {token_account}: {balance}")
                    return balance
                else:
                    logger.warning(f"No token balance data returned for {token_account}")
                    return None
            except RPCException as e:
                error_msg = str(e)
                # If account doesn't exist, it means balance is 0 (token account not created yet)
                if "could not find account" in error_msg.lower():
                    logger.info(f"Token account {token_account} does not exist yet (balance: 0.0)")
                    return 0.0
                retries += 1
                logger.warning(f"RPC error getting token balance (attempt {retries}/{self.max_retries}): {e}")
                if retries < self.max_retries:
                    time.sleep(delay)
                    delay = min(delay * 2, 60)
            except Exception as e:
                logger.error(f"Unexpected error getting token balance: {e}")
                return None

        logger.error(f"Failed to get token balance after {self.max_retries} attempts")
        return None

    def send_transaction(self, signed_tx: bytes) -> Optional[str]:
        """
        Send a signed transaction to the network.

        Args:
            signed_tx: Serialized signed transaction

        Returns:
            Transaction signature, or None if sending fails
        """
        if not self.client:
            logger.error("Client not initialized")
            return None

        retries = 0
        delay = self.retry_delay

        while retries < self.max_retries:
            try:
                response = self.client.send_raw_transaction(signed_tx)
                if response.value:
                    signature = str(response.value)
                    logger.info(f"Transaction sent successfully: {signature}")
                    return signature
                else:
                    logger.warning("No signature returned from transaction submission")
                    return None
            except RPCException as e:
                retries += 1
                logger.warning(f"RPC error sending transaction (attempt {retries}/{self.max_retries}): {e}")
                if retries < self.max_retries:
                    time.sleep(delay)
                    delay = min(delay * 2, 60)
            except Exception as e:
                logger.error(f"Unexpected error sending transaction: {e}")
                return None

        logger.error(f"Failed to send transaction after {self.max_retries} attempts")
        return None

    def confirm_transaction(
        self, signature: str, max_wait_seconds: int = 30, poll_interval: float = 1.0
    ) -> bool:
        """
        Wait for a transaction to be confirmed on the blockchain.

        Args:
            signature: Transaction signature to wait for
            max_wait_seconds: Maximum time to wait for confirmation
            poll_interval: Time between status checks in seconds

        Returns:
            True if transaction confirmed, False if timeout or error
        """
        if not self.client:
            logger.error("Client not initialized")
            return False

        logger.info(f"Waiting for transaction confirmation: {signature[:16]}...")
        start_time = time.time()

        # Convert string signature to Signature object
        sig_obj = Signature.from_string(signature)

        while (time.time() - start_time) < max_wait_seconds:
            try:
                # Check transaction status
                response = self.client.get_signature_statuses([sig_obj])

                if response.value and len(response.value) > 0:
                    status = response.value[0]

                    if status is not None:
                        # Check if transaction is confirmed
                        if status.confirmation_status:
                            confirmation_level = str(status.confirmation_status)
                            logger.info(f"Transaction confirmation status: {confirmation_level}")

                            # Accept 'confirmed' or 'finalized'
                            # Check if the status contains these keywords
                            if "Confirmed" in confirmation_level or "Finalized" in confirmation_level:
                                logger.info(f"Transaction confirmed after {time.time() - start_time:.2f}s")
                                return True

                        # Check for errors
                        if status.err:
                            logger.error(f"Transaction failed with error: {status.err}")
                            return False

                # Wait before next check
                time.sleep(poll_interval)

            except Exception as e:
                logger.warning(f"Error checking transaction status: {e}")
                time.sleep(poll_interval)

        logger.warning(f"Transaction confirmation timeout after {max_wait_seconds}s")
        return False
