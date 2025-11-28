"""
Trading execution via Jupiter aggregator.
"""

import time
from typing import Optional, Dict, Any

import requests
import base64

from solders.keypair import Keypair

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
        jupiter_quote_api: str = "https://quote-api.jup.ag/v6/quote",
        jupiter_swap_api: str = "https://quote-api.jup.ag/v6/swap",
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize Jupiter trader.

        Args:
            rpc_client: Solana RPC client
            keypair: Wallet keypair for signing transactions
            jupiter_quote_api: Jupiter quote API endpoint
            jupiter_swap_api: Jupiter swap API endpoint
            max_retries: Maximum retry attempts for API calls
            retry_delay: Initial delay between retries in seconds
        """
        self.rpc_client = rpc_client
        self.keypair = keypair
        self.jupiter_quote_api = jupiter_quote_api
        self.jupiter_swap_api = jupiter_swap_api
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
            "asLegacyTransaction": "false",
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
            swap_response = self._get_swap_transaction(quote)
            if not swap_response:
                logger.error("Failed to get swap transaction from Jupiter")
                return None

            swap_transaction = swap_response.get("swapTransaction")
            if not swap_transaction:
                logger.error("No swap transaction in response")
                return None

            transaction_bytes = base64.b64decode(swap_transaction)

            signature = self.rpc_client.send_transaction(transaction_bytes)

            if signature:
                logger.info(f"Swap executed successfully. Signature: {signature}")
                logger.info(f"View on Solscan: https://solscan.io/tx/{signature}")
                return signature
            else:
                logger.error("Failed to send swap transaction")
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
    ) -> Optional[str]:
        """
        Buy SOL with USDC.

        Args:
            usdc_amount: Amount of USDC to spend
            usdc_mint: USDC token mint address
            sol_mint: SOL token mint address
            max_slippage_percent: Maximum slippage percentage

        Returns:
            Transaction signature, or None if trade fails
        """
        logger.info(f"Initiating BUY: {usdc_amount} USDC -> SOL")

        amount_in_smallest_unit = int(usdc_amount * 1e6)
        slippage_bps = int(max_slippage_percent * 100)

        quote = self.get_quote(
            input_mint=usdc_mint,
            output_mint=sol_mint,
            amount=amount_in_smallest_unit,
            slippage_bps=slippage_bps,
        )

        if not quote:
            logger.error("Failed to get quote for BUY order")
            return None

        return self.execute_swap(quote, max_slippage_percent)

    def sell_sol_for_usdc(
        self,
        sol_amount: float,
        sol_mint: str,
        usdc_mint: str,
        max_slippage_percent: float = 1.0,
    ) -> Optional[str]:
        """
        Sell SOL for USDC.

        Args:
            sol_amount: Amount of SOL to sell
            sol_mint: SOL token mint address
            usdc_mint: USDC token mint address
            max_slippage_percent: Maximum slippage percentage

        Returns:
            Transaction signature, or None if trade fails
        """
        logger.info(f"Initiating SELL: {sol_amount} SOL -> USDC")

        amount_in_smallest_unit = int(sol_amount * 1e9)
        slippage_bps = int(max_slippage_percent * 100)

        quote = self.get_quote(
            input_mint=sol_mint,
            output_mint=usdc_mint,
            amount=amount_in_smallest_unit,
            slippage_bps=slippage_bps,
        )

        if not quote:
            logger.error("Failed to get quote for SELL order")
            return None

        return self.execute_swap(quote, max_slippage_percent)
