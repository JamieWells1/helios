"""
Trading execution via Jupiter aggregator.
"""

import os
import time
from typing import Optional, Dict, Any

import requests
import base64

from solders.keypair import Keypair
from solders.transaction import VersionedTransaction, Transaction
from solders.message import MessageV0, to_bytes_versioned
from solders.signature import Signature

from .client import SolanaClient
from ..utils.logging import get_logger

logger = get_logger(__name__)


class JupiterTrader:
    """
    Executes trades via Jupiter aggregator V6 API.
    """

    def __init__(
        self,
        rpc_client: SolanaClient,
        keypair: Keypair,
        jupiter_quote_api: Optional[str] = None,
        jupiter_swap_api: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize Jupiter trader.

        Args:
            rpc_client: Solana RPC client
            keypair: Wallet keypair for signing transactions
            jupiter_quote_api: Jupiter quote API endpoint (defaults to env var JUPITER_QUOTE_API)
            jupiter_swap_api: Jupiter swap API endpoint (defaults to env var JUPITER_SWAP_API)
            max_retries: Maximum retry attempts for API calls
            retry_delay: Initial delay between retries in seconds
        """
        self.rpc_client = rpc_client
        self.keypair = keypair

        # Load from environment variables with fallback to public endpoints
        self.jupiter_quote_api = jupiter_quote_api or os.getenv(
            "JUPITER_QUOTE_API", "https://public.jupiterapi.com/quote"
        )
        self.jupiter_swap_api = jupiter_swap_api or os.getenv(
            "JUPITER_SWAP_API", "https://public.jupiterapi.com/swap"
        )

        self.max_retries = max_retries
        self.retry_delay = retry_delay

        logger.info(f"Jupiter trader initialized (quote: {self.jupiter_quote_api}, swap: {self.jupiter_swap_api})")

    def get_quote(
        self, input_mint: str, output_mint: str, amount: int, slippage_bps: int = 100
    ) -> Optional[Dict[str, Any]]:
        """
        Get a quote for a swap from Jupiter.

        Args:
            input_mint: Input token mint address
            output_mint: Output token mint address
            amount: Amount in smallest unit (e.g., lamports for SOL)
            slippage_bps: Slippage tolerance in basis points (100 = 1%)

        Returns:
            Quote data dictionary, or None if request fails
        """
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": str(slippage_bps),
            "onlyDirectRoutes": "false",
            "asLegacyTransaction": "true",
        }

        retries = 0
        delay = self.retry_delay

        while retries < self.max_retries:
            try:
                response = requests.get(
                    self.jupiter_quote_api, params=params, timeout=10
                )
                response.raise_for_status()
                quote = response.json()

                logger.info(
                    f"Got quote: {amount} {input_mint[:8]}... -> "
                    f"{quote.get('outAmount', 'N/A')} {output_mint[:8]}..."
                )
                return quote

            except requests.exceptions.RequestException as e:
                retries += 1
                logger.warning(
                    f"Failed to get quote (attempt {retries}/{self.max_retries}): {e}"
                )
                if retries < self.max_retries:
                    time.sleep(delay)
                    delay = min(delay * 2, 60)
            except Exception as e:
                logger.error(f"Unexpected error getting quote: {e}")
                return None

        logger.error(f"Failed to get quote after {self.max_retries} attempts")
        return None

    def execute_swap(
        self, quote: Dict[str, Any], max_slippage_percent: float = 1.0
    ) -> Optional[str]:
        """
        Execute a swap using a quote from Jupiter.

        Args:
            quote: Quote data from get_quote()
            max_slippage_percent: Maximum slippage percentage

        Returns:
            Transaction signature, or None if swap fails
        """
        try:
            # Get swap transaction from Jupiter immediately
            # This minimizes the time between quote and execution
            swap_response = self._get_swap_transaction(quote)
            if not swap_response:
                logger.error("Failed to get swap transaction from Jupiter")
                return None

            swap_transaction = swap_response.get("swapTransaction")
            if not swap_transaction:
                logger.error("No swap transaction in response")
                return None

            # Check for simulation error (indicates quote may be stale)
            simulation_error = swap_response.get("simulationError")
            if simulation_error:
                logger.warning(f"Jupiter simulation error: {simulation_error}")
                logger.info("This may indicate the quote has expired or slippage exceeded")

            # Log the swap response keys to understand what Jupiter returns
            logger.info(f"Swap response keys: {list(swap_response.keys())}")

            # Decode the base64 transaction from Jupiter
            transaction_bytes = base64.b64decode(swap_transaction)
            logger.info(f"Decoded transaction, {len(transaction_bytes)} bytes")

            # Decode and sign the transaction from Jupiter
            try:
                tx = VersionedTransaction.from_bytes(transaction_bytes)
                logger.info(f"Transaction has {len(tx.signatures)} signature slot(s)")

                # Check if first signature is placeholder (all zeros)
                first_sig_bytes = bytes(tx.signatures[0])
                zero_sig = bytes(64)
                is_signed = first_sig_bytes != zero_sig

                if is_signed:
                    logger.info("Transaction already signed - sending as-is")
                    signature = self.rpc_client.send_transaction(transaction_bytes)
                    if signature:
                        logger.info(f"Swap executed successfully. Signature: {signature}")
                        logger.info(f"View on Solscan: https://solscan.io/tx/{signature}")
                    return signature

                # Transaction needs signing - do this immediately to minimize delay
                logger.info("Signing transaction with keypair...")

                # Get the message from the transaction
                message = tx.message

                # Sign the versioned message using the correct method
                # to_bytes_versioned() serializes the message in the correct format for signing
                signature_obj = self.keypair.sign_message(to_bytes_versioned(message))

                logger.info(f"Created signature: {bytes(signature_obj)[:16].hex()}...")

                # Populate the transaction with the signature
                # VersionedTransaction.populate() creates a properly signed transaction
                signed_tx = VersionedTransaction.populate(message, [signature_obj])

                logger.info(f"Populated transaction with signature")

                # Send the signed transaction immediately
                signature = self.rpc_client.send_transaction(bytes(signed_tx))
                if signature:
                    logger.info(f"Swap executed successfully. Signature: {signature}")
                    logger.info(f"View on Solscan: https://solscan.io/tx/{signature}")
                return signature

            except Exception as e:
                logger.error(f"Error processing transaction: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return None

        except Exception as e:
            logger.error(f"Error executing swap: {e}")
            return None

    def _get_swap_transaction(self, quote: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get swap transaction from Jupiter.

        Args:
            quote: Quote data

        Returns:
            Swap transaction response, or None if request fails
        """
        payload = {
            "quoteResponse": quote,
            "userPublicKey": str(self.keypair.pubkey()),
            "wrapAndUnwrapSol": True,
            "dynamicComputeUnitLimit": True,
            "prioritizationFeeLamports": "auto",
        }

        retries = 0
        delay = self.retry_delay

        while retries < self.max_retries:
            try:
                response = requests.post(
                    self.jupiter_swap_api, json=payload, timeout=10
                )
                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                retries += 1
                logger.warning(
                    f"Failed to get swap transaction (attempt {retries}/{self.max_retries}): {e}"
                )
                if retries < self.max_retries:
                    time.sleep(delay)
                    delay = min(delay * 2, 60)
            except Exception as e:
                logger.error(f"Unexpected error getting swap transaction: {e}")
                return None

        logger.error(
            f"Failed to get swap transaction after {self.max_retries} attempts"
        )
        return None

    def buy_sol_with_usdc(
        self,
        usdc_amount: float,
        usdc_mint: str,
        sol_mint: str,
        max_slippage_percent: float = 1.0,
        max_quote_retries: int = 2,
    ) -> Optional[str]:
        """
        Buy SOL with USDC with automatic quote refresh on expiration.

        Args:
            usdc_amount: Amount of USDC to spend
            usdc_mint: USDC token mint address
            sol_mint: SOL token mint address
            max_slippage_percent: Maximum slippage percentage
            max_quote_retries: Number of times to retry with fresh quote on expiration

        Returns:
            Transaction signature, or None if trade fails
        """
        logger.info(f"Initiating BUY: {usdc_amount} USDC -> SOL")

        amount_in_smallest_unit = int(usdc_amount * 1e6)
        slippage_bps = int(max_slippage_percent * 100)

        # Retry loop for quote expiration
        for attempt in range(max_quote_retries + 1):
            if attempt > 0:
                logger.info(f"Retrying with fresh quote (attempt {attempt + 1}/{max_quote_retries + 1})...")
                time.sleep(0.5)  # Brief pause before retry

            # Get fresh quote
            quote = self.get_quote(
                input_mint=usdc_mint,
                output_mint=sol_mint,
                amount=amount_in_smallest_unit,
                slippage_bps=slippage_bps,
            )

            if not quote:
                logger.error("Failed to get quote for BUY order")
                continue

            # Execute immediately to minimize time between quote and swap
            result = self.execute_swap(quote, max_slippage_percent)

            if result:
                return result

            # If execution failed, it might be due to quote expiration - retry with fresh quote
            logger.warning("Swap execution failed, will retry with fresh quote if attempts remain")

        logger.error(f"Failed to execute BUY after {max_quote_retries + 1} attempts")
        return None

    def sell_sol_for_usdc(
        self,
        sol_amount: float,
        sol_mint: str,
        usdc_mint: str,
        max_slippage_percent: float = 1.0,
        max_quote_retries: int = 2,
    ) -> Optional[str]:
        """
        Sell SOL for USDC with automatic quote refresh on expiration.

        Args:
            sol_amount: Amount of SOL to sell
            sol_mint: SOL token mint address
            usdc_mint: USDC token mint address
            max_slippage_percent: Maximum slippage percentage
            max_quote_retries: Number of times to retry with fresh quote on expiration

        Returns:
            Transaction signature, or None if trade fails
        """
        logger.info(f"Initiating SELL: {sol_amount} SOL -> USDC")

        amount_in_smallest_unit = int(sol_amount * 1e9)
        slippage_bps = int(max_slippage_percent * 100)

        # Retry loop for quote expiration
        for attempt in range(max_quote_retries + 1):
            if attempt > 0:
                logger.info(f"Retrying with fresh quote (attempt {attempt + 1}/{max_quote_retries + 1})...")
                time.sleep(0.5)  # Brief pause before retry

            # Get fresh quote
            quote = self.get_quote(
                input_mint=sol_mint,
                output_mint=usdc_mint,
                amount=amount_in_smallest_unit,
                slippage_bps=slippage_bps,
            )

            if not quote:
                logger.error("Failed to get quote for SELL order")
                continue

            # Execute immediately to minimize time between quote and swap
            result = self.execute_swap(quote, max_slippage_percent)

            if result:
                return result

            # If execution failed, it might be due to quote expiration - retry with fresh quote
            logger.warning("Swap execution failed, will retry with fresh quote if attempts remain")

        logger.error(f"Failed to execute SELL after {max_quote_retries + 1} attempts")
        return None
