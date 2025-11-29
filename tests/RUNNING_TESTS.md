# Running Tests - Quick Reference

## Recent Updates

**Jupiter API Fix (Nov 2025)**: Updated to use `https://public.jupiterapi.com` endpoints. The old `quote-api.jup.ag` domain was deprecated and no longer resolves. See [JUPITER_API_UPDATE.md](../JUPITER_API_UPDATE.md) for details.

## Safe Tests (No Real Transactions)

These tests use SQLite and mock data - they're completely safe to run anytime.

### Option 1: Run in Docker (Recommended)
```bash
docker-compose run --rm bot-test ./run_tests.sh
```

### Option 2: Run Locally
```bash
# First install dependencies
pip install -r requirements.txt

# Then run tests
./run_tests.sh
# OR
python3 -m unittest tests.test_candle_store -v
```

## Trading Tests (⚠️ REAL TRANSACTIONS!)

These tests execute actual blockchain transactions with real funds.

**Prerequisites:**
- Funded wallet (at least 0.5 SOL + $25 USDC)
- `.env` file configured with `SOLANA_RPC_URL` and `WALLET_PRIVATE_KEY`
- Understanding that these cost real money (~$0.14-$0.30 per run)

### Option 1: Run in Docker (Recommended)
```bash
docker-compose run --rm bot-test ./run_trading_tests.sh
```

### Option 2: Run Locally
```bash
# First install dependencies
pip install -r requirements.txt

# Then run trading tests
./run_trading_tests.sh
# OR
python3 -m unittest tests.test_trading -v
```

### Run Specific Trading Test

**Just check balances (safe, no trades):**
```bash
python3 -m unittest tests.test_trading.TestTrading.test_1_check_balances -v
```

**Just the buy test:**
```bash
python3 -m unittest tests.test_trading.TestTrading.test_2_buy_sol -v
```

**Just the sell test:**
```bash
python3 -m unittest tests.test_trading.TestTrading.test_3_sell_sol -v
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'base58'"

**Problem:** Dependencies not installed locally.

**Solution:** Either:
1. Install dependencies: `pip install -r requirements.txt`
2. Use Docker (dependencies pre-installed): `docker-compose run --rm bot-test ...`

### "Insufficient USDC balance"

**Problem:** Not enough USDC in wallet for trading tests.

**Solution:** Add at least $25 USDC to your wallet.

### "Failed to get quote"

**Problem:** RPC endpoint issues or rate limiting.

**Solution:**
- Check your `SOLANA_RPC_URL` in `.env`
- Try a different RPC endpoint (Helius, QuickNode)
- Wait a minute and try again

## Viewing Results

All tests log detailed output including:
- Initial balances
- Trade execution (buy/sell with amounts)
- Transaction signatures
- Final balances
- Solscan URLs for verification

Example Solscan URL format:
```
https://solscan.io/tx/<transaction_signature>
```

Copy the signature from the logs and paste it in your browser to see the transaction details on-chain.
