# Trading Tests Documentation

## Overview

The `test_trading.py` file contains integration tests that execute **real trades** on the Solana blockchain using the Jupiter aggregator. These tests verify that the buy and sell logic works correctly end-to-end.

## ⚠️ IMPORTANT WARNINGS

1. **REAL MONEY**: These tests execute actual blockchain transactions with real funds
2. **TRANSACTION FEES**: Each test will incur Solana network fees (~0.0001-0.001 SOL per transaction)
3. **SLIPPAGE**: Trades are subject to market slippage (configured at 1% max)
4. **MAINNET ONLY**: These tests are designed for mainnet-beta (can be adapted for devnet)

## Test Structure

### Test 1: `test_1_check_balances`
- Verifies wallet has sufficient SOL and USDC balances
- Checks minimum requirements before trading
- **No trades executed**

### Test 2: `test_2_buy_sol`
- **Buys ~0.1 SOL using $20 USDC**
- Executes real buy order via Jupiter
- Waits 5 seconds for confirmation
- Verifies balances changed correctly
- **Real money transaction!**

### Test 3: `test_3_sell_sol`
- **Sells 0.1 SOL for USDC**
- Executes real sell order via Jupiter
- Waits 5 seconds for confirmation
- Verifies balances changed correctly
- **Real money transaction!**

## Prerequisites

Before running these tests, ensure:

1. **Funded Wallet**
   - At least 0.5 SOL (for fees and buffer)
   - At least $25 USDC (for the buy test)

2. **Environment Variables**
   ```bash
   SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
   WALLET_PRIVATE_KEY=<your_base58_private_key>
   SOL_MINT=So11111111111111111111111111111111111111112
   USDC_MINT=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
   ```

3. **Dependencies Installed**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Tests

### Option 1: Run All Trading Tests
```bash
python3 -m unittest tests/test_trading.py -v
```

### Option 2: Run Specific Test
```bash
# Just check balances (safe, no trades)
python3 -m unittest tests.test_trading.TestTrading.test_1_check_balances -v

# Run buy test only
python3 -m unittest tests.test_trading.TestTrading.test_2_buy_sol -v

# Run sell test only
python3 -m unittest tests.test_trading.TestTrading.test_3_sell_sol -v
```

### Option 3: Run with Docker
```bash
# Build and run in container
docker-compose run --rm bot-test python3 -m unittest tests/test_trading.py -v
```

## Expected Output

Successful test output will show:

```
======================================================================
SETTING UP TRADING TESTS
======================================================================
Initializing Solana client...
Initializing wallet...
Initializing Jupiter trader...
SOL mint: So11111111111111111111111111111111111111112
USDC mint: EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
Test amount: 0.1 SOL
======================================================================

======================================================================
STARTING TEST: test_2_buy_sol
======================================================================
======================================================================
TEST 1: BUY 0.1 SOL WITH USDC
======================================================================
Initial SOL balance: 1.2345 SOL
Initial USDC balance: 150.00 USDC
Attempting to buy ~0.1 SOL with 20.0 USDC...
Initiating BUY: 20.0 USDC -> SOL
Got quote: 20000000 EPjFWdd5... -> 98765432 So111111...
Swap executed successfully. Signature: 5KqR7...
View on Solscan: https://solscan.io/tx/5KqR7...
✓ BUY ORDER SUCCESSFUL
✓ Transaction signature: 5KqR7...
✓ View on Solscan: https://solscan.io/tx/5KqR7...
Waiting 5 seconds for transaction to confirm...

TRADE RESULTS:
  SOL gained: +0.0987 SOL
  USDC spent: -20.00 USDC
  Final SOL balance: 1.3332 SOL
  Final USDC balance: 130.00 USDC
✓ Test passed
```

## Verification

After running tests, you can verify transactions on Solscan:

1. Copy the transaction signature from the test output
2. Visit: `https://solscan.io/tx/<signature>`
3. Verify the trade details, amounts, and fees

## Safety Recommendations

### For Testing on Mainnet:
1. **Use a separate test wallet** with minimal funds
2. **Start with the balance check** to ensure you have enough
3. **Run tests during low-volatility periods** to minimize slippage
4. **Monitor the first trade** manually before running full suite

### For Production Use:
1. **Test on Devnet first** (requires modifying mint addresses)
2. **Use a dedicated wallet** for the trading bot
3. **Set conservative position sizes** in your `.env`
4. **Monitor continuously** with logging

## Troubleshooting

### Test Fails: "Insufficient USDC balance"
- **Solution**: Add more USDC to your wallet (minimum $25)

### Test Fails: "Failed to get quote" or DNS Resolution Error
- **Solution**: Ensure you're using the correct Jupiter API endpoints
  - Quote API: `https://public.jupiterapi.com/quote`
  - Swap API: `https://public.jupiterapi.com/swap`
- **Possible Cause**: Rate limiting, network issues, or outdated API endpoints
- **Note**: The old `quote-api.jup.ag` domain was deprecated. The bot now uses `public.jupiterapi.com`

### Test Fails: "Insufficient SOL balance"
- **Solution**: Add more SOL for transaction fees (recommend 0.5+ SOL)

### Transaction Confirms but Balances Don't Change
- **Wait Longer**: Try increasing the 5-second wait time
- **Check Solscan**: Transaction may be confirmed but not reflected yet

## Cost Estimate

Running the full test suite (buy + sell):
- **Solana Transaction Fees**: ~0.00025 SOL × 2 = ~$0.10
- **Jupiter Platform Fees**: $0.00 (Jupiter doesn't charge fees!)
- **Slippage** (actual market movement):
  - Max allowed: 1% × $20 = $0.20
  - Typical on SOL/USDC: 0.1-0.3% × $20 = $0.02-$0.06
- **Total Cost**: ~$0.14-$0.30 (realistically ~$0.20)

## Integration with CI/CD

**DO NOT** run these tests in automated CI/CD pipelines unless:
1. You have a dedicated test wallet with controlled funds
2. You're okay with automated spending
3. You have alerts set up for failures

For CI/CD, use the mock/unit tests instead:
```bash
python3 -m unittest discover -s tests -p "test_*.py" --exclude test_trading.py
```

## Code Review Checklist

Before running these tests, verify:

- [ ] Wallet private key is correct and funded
- [ ] RPC endpoint is reliable (paid tier recommended)
- [ ] Position sizes are appropriate ($20 USDC, 0.1 SOL)
- [ ] Slippage tolerance is acceptable (1% default)
- [ ] You understand these are REAL trades with REAL money
- [ ] You've reviewed the transaction logs will be clear

## Related Files

- `src/blockchain/trader.py` - Trading execution logic
- `src/blockchain/wallet.py` - Wallet management
- `src/blockchain/client.py` - RPC client
- `src/main.py` - Main bot that calls these functions
