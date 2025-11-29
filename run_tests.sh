#!/bin/bash

# This script runs safe unittests (excludes trading tests that execute real transactions)

# Exit immediately if a command exits with a non-zero status
set -e

echo "Running safe tests (excluding test_trading.py)..."
echo "To run trading tests, use: ./run_trading_tests.sh"
echo ""

# Run only candle store tests (safe, no real transactions)
python3 -m unittest tests.test_candle_store -v
