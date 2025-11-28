#!/bin/bash

WALLET="DN9UJJD88hi1tsam4r2wAZfDRJcMRCLfnAinTQfHsQWg"
USDC_MINT="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

echo "=== Wallet Balances ==="
echo ""
echo "SOL Balance:"
solana balance $WALLET --url mainnet-beta
echo ""
echo "USDC Balance:"
spl-token balance $USDC_MINT --owner $WALLET --url mainnet-beta
echo ""
echo "Full token list:"
spl-token accounts --owner $WALLET --url mainnet-beta
