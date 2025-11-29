#!/bin/bash

# ⚠️  WARNING: This script executes REAL trades with REAL money!
# Only run this if you understand the risks and costs involved.

# Exit immediately if a command exits with a non-zero status
set -e

echo "======================================================================"
echo "⚠️  WARNING: TRADING TESTS EXECUTE REAL BLOCKCHAIN TRANSACTIONS"
echo "======================================================================"
echo ""
echo "These tests will:"
echo "  - Buy ~0.1 SOL using \$20 USDC"
echo "  - Sell 0.1 SOL for USDC"
echo "  - Incur Solana transaction fees (~\$0.10 total)"
echo "  - Subject to market slippage (~\$0.02-\$0.06)"
echo ""
echo "Estimated cost: \$0.14-\$0.30 per full test run"
echo ""
echo "Press Ctrl+C within 10 seconds to cancel..."
echo ""

# Give user time to cancel
sleep 10

echo "Running trading tests..."
echo ""

# Run all trading tests in order
python3 -m unittest tests.test_trading -v

echo ""
echo "======================================================================"
echo "Trading tests completed!"
echo "======================================================================"
