# Solana Trading Bot

A production-ready algorithmic trading bot for intraday trading on Solana. The bot executes trades on SOL/USDC via the Jupiter aggregator based on user-defined strategies.

## Features

- **Automated Trading**: Continuous monitoring and execution of trades based on strategy signals
- **Jupiter Integration**: Optimal trade routing through Jupiter V6 aggregator
- **Multiple Price Sources**: Aggregates prices from CoinGecko and Jupiter APIs
- **Strategy Framework**: Extensible strategy system with example moving average crossover implementation
- **Robust Error Handling**: Automatic reconnection, exponential backoff, and graceful failure recovery
- **State Persistence**: Position tracking survives restarts via JSON state files
- **Comprehensive Logging**: Detailed logs with rotation for monitoring and debugging
- **Docker Support**: Containerized deployment for consistent operation
- **Production Ready**: Built with safety features, validation, and operational stability in mind

## Project Structure

```
helios/
├── src/
│   ├── blockchain/          # Solana blockchain integration
│   │   ├── client.py       # RPC client with health checking
│   │   ├── wallet.py       # Wallet management and balance queries
│   │   └── trader.py       # Jupiter trading execution
│   ├── data/
│   │   └── price_feed.py   # Multi-source price aggregation
│   ├── strategies/
│   │   ├── base.py         # Abstract strategy base class
│   │   └── moving_average.py  # Example MA crossover strategy
│   ├── utils/
│   │   ├── logging.py      # Logging configuration
│   │   └── state.py        # State persistence
│   └── main.py             # Main application entry point
├── logs/                    # Log files (auto-created)
├── data/                    # State persistence (auto-created)
├── Dockerfile              # Docker image configuration
├── docker-compose.yml      # Docker Compose orchestration
├── requirements.txt        # Python dependencies
├── .env.example           # Example environment configuration
└── README.md              # This file
```

## Prerequisites

- **Docker & Docker Compose** (recommended) OR Python 3.13+
- **Solana Wallet** with private key
- **RPC Endpoint** (e.g., Helius, QuickNode, or public endpoint)
- **Funded Wallet** with SOL (for fees) and USDC (for trading)

## Quick Start

### 1. Environment Setup

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` and set your configuration:

```bash
# Required: Your Solana RPC endpoint
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# Required: Your wallet private key (Base58 encoded)
PRIVATE_KEY=your_base58_private_key_here

# Position sizing (amount to trade per signal)
POSITION_SIZE_USDC=100

# Other settings have sensible defaults
```

**IMPORTANT**: Keep your `.env` file secure. Never commit it to version control.

### 2. Running with Docker (Recommended)

Build and start the bot:

```bash
docker-compose up --build
```

Run in detached mode:

```bash
docker-compose up -d
```

View logs:

```bash
docker-compose logs -f
```

Stop the bot:

```bash
docker-compose down
```

### 3. Running Locally (Alternative)

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the bot:

```bash
python main.py
```

## Configuration

All configuration is done through environment variables in the `.env` file.

### Required Settings

| Variable         | Description                       |
| ---------------- | --------------------------------- |
| `SOLANA_RPC_URL` | Solana RPC endpoint URL           |
| `PRIVATE_KEY`    | Base58 encoded wallet private key |

### Trading Settings

| Variable                 | Default | Description                          |
| ------------------------ | ------- | ------------------------------------ |
| `POSITION_SIZE_USDC`     | 100     | USDC amount per trade                |
| `MAX_POSITION_SIZE_USDC` | 1000    | Maximum position size limit          |
| `MAX_SLIPPAGE_PERCENT`   | 1.0     | Maximum acceptable slippage (%)      |
| `CHECK_INTERVAL_SECONDS` | 10      | Seconds between strategy evaluations |

### Strategy Settings

| Variable          | Default                | Description                       |
| ----------------- | ---------------------- | --------------------------------- |
| `STRATEGY_NAME`   | MovingAverageCrossover | Strategy to use                   |
| `MA_SHORT_PERIOD` | 5                      | Short MA period (for MA strategy) |
| `MA_LONG_PERIOD`  | 20                     | Long MA period (for MA strategy)  |

### Price Feed Settings

| Variable              | Default | Description                   |
| --------------------- | ------- | ----------------------------- |
| `USE_COINGECKO`       | true    | Enable CoinGecko price source |
| `USE_JUPITER`         | true    | Enable Jupiter price source   |
| `PRICE_CACHE_SECONDS` | 5       | Price cache duration          |

### Logging Settings

| Variable             | Default  | Description                                       |
| -------------------- | -------- | ------------------------------------------------- |
| `LOG_LEVEL`          | INFO     | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `MAX_LOG_SIZE_BYTES` | 10485760 | Max log file size (10MB)                          |
| `LOG_BACKUP_COUNT`   | 5        | Number of backup log files                        |

## Implementing Custom Strategies

The bot is designed to make implementing custom strategies simple.

### 1. Create Your Strategy

Create a new file in `src/strategies/` (e.g., `my_strategy.py`):

```python
from typing import Dict, Any
from .base import BaseStrategy

class MyStrategy(BaseStrategy):
    """Your custom strategy implementation."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Initialize your strategy variables

    def update(self, current_price: float) -> None:
        """Update strategy with new price data."""
        # Update your indicators, calculations, etc.
        pass

    def should_buy(self, current_price: float) -> bool:
        """Return True when conditions for buying are met."""
        # Implement your buy logic
        return False

    def should_sell(self, current_price: float) -> bool:
        """Return True when conditions for selling are met."""
        # Implement your sell logic
        return False
```

### 2. Register Your Strategy

Edit `src/main.py` and add your strategy to the `strategies` dictionary in the `_create_strategy` method:

```python
def _create_strategy(self, strategy_name: str) -> BaseStrategy:
    strategies = {
        'MovingAverageCrossover': MovingAverageCrossover,
        'MyStrategy': MyStrategy,  # Add your strategy here
    }
    # ... rest of the method
```

### 3. Configure to Use Your Strategy

Update your `.env` file:

```bash
STRATEGY_NAME=MyStrategy
```

That's it! Restart the bot and it will use your custom strategy.

## Monitoring

### Viewing Logs

Logs are written to both the console and rotating files in the `logs/` directory.

With Docker:

```bash
docker-compose logs -f
```

With local installation:

```bash
tail -f logs/trading_bot.log
```

### Understanding Log Messages

The bot logs:

- Application startup and shutdown
- Configuration loading
- Price fetches from all sources
- Balance checks before trades
- Strategy signals (BUY, SELL, HOLD)
- Trade executions with transaction signatures
- Errors with full stack traces
- State changes and persistence

### Checking Bot State

The bot's current position and state are saved in `data/bot_state.json`:

```bash
cat data/bot_state.json
```

Example state:

```json
{
  "position": "long",
  "entry_price": 125.43,
  "entry_time": "2025-01-15T10:30:00",
  "entry_amount_usdc": 100.0,
  "last_updated": "2025-01-15T10:30:05",
  "strategy_state": {
    "price_history": [124.5, 125.1, 125.43],
    "prev_short_ma": 125.01,
    "prev_long_ma": 124.8
  }
}
```

## Testing

### Testing on Devnet

Before running with real capital, test on Solana devnet:

1. Get devnet SOL and USDC from faucets
2. Update your `.env`:
   ```bash
   SOLANA_RPC_URL=https://api.devnet.solana.com
   SOL_MINT=So11111111111111111111111111111111111111112
   USDC_MINT=<devnet_usdc_mint>
   ```
3. Run the bot and verify it operates correctly

### Start Small

When moving to mainnet:

1. Start with very small `POSITION_SIZE_USDC` (e.g., 10)
2. Monitor for several hours/days
3. Verify trades execute as expected
4. Gradually increase position size as you gain confidence

## Safety Features

The bot includes multiple safety mechanisms:

- **Balance Validation**: Checks sufficient balance before every trade
- **Slippage Protection**: Enforces maximum slippage tolerance
- **Position Limits**: Respects maximum position size configuration
- **State Persistence**: Tracks positions across restarts
- **Sanity Checks**: Prevents buying when already long, selling when flat
- **Graceful Shutdown**: Saves state before exiting
- **Error Recovery**: Continues operation despite transient failures

## Troubleshooting

### Bot Won't Start

**Issue**: Missing configuration

- **Solution**: Verify all required fields in `.env` are set

**Issue**: Invalid private key

- **Solution**: Ensure private key is Base58 encoded and valid

### Trades Not Executing

**Issue**: Insufficient balance

- **Solution**: Check wallet balances with `get_sol_balance()` and `get_usdc_balance()`

**Issue**: RPC errors

- **Solution**: Use a reliable paid RPC provider (Helius, QuickNode)

**Issue**: Slippage too restrictive

- **Solution**: Increase `MAX_SLIPPAGE_PERCENT` slightly

### Price Fetch Failures

**Issue**: Rate limiting

- **Solution**: Increase `CHECK_INTERVAL_SECONDS` to reduce API calls

**Issue**: API unavailable

- **Solution**: Ensure both CoinGecko and Jupiter sources are enabled

### High Fees

**Issue**: Frequent trading

- **Solution**: Increase `CHECK_INTERVAL_SECONDS` or adjust strategy parameters

## Common Workflows

### Update Strategy Parameters

1. Stop the bot: `docker-compose down`
2. Edit `.env` to change parameters (e.g., `MA_SHORT_PERIOD`, `MA_LONG_PERIOD`)
3. Restart: `docker-compose up -d`

### Switch Strategies

1. Implement new strategy (see "Implementing Custom Strategies")
2. Update `STRATEGY_NAME` in `.env`
3. Restart the bot

### Reset Bot State

To start fresh (clears position history):

```bash
rm data/bot_state.json
docker-compose restart
```

**Warning**: Only do this when you have no open positions!

### View Transaction on Solscan

Transaction signatures are logged. View them on Solscan:

```
https://solscan.io/tx/<transaction_signature>
```

## Architecture

### Components

1. **Blockchain Layer** (`src/blockchain/`)

   - `client.py`: Manages Solana RPC connections
   - `wallet.py`: Handles keypair and balance queries
   - `trader.py`: Executes swaps via Jupiter

2. **Data Layer** (`src/data/`)

   - `price_feed.py`: Aggregates prices from multiple sources with caching

3. **Strategy Layer** (`src/strategies/`)

   - `base.py`: Abstract base class defining strategy interface
   - `moving_average.py`: Example implementation

4. **Utilities** (`src/utils/`)

   - `logging.py`: Configures rotating file and console logging
   - `state.py`: Handles atomic state persistence to JSON

5. **Main Application** (`src/main.py`)
   - Orchestrates all components
   - Runs main trading loop
   - Handles signals and graceful shutdown

### Data Flow

```
Price Sources (CoinGecko, Jupiter)
    |
    v
Price Feed (with caching)
    |
    v
Strategy (evaluates signals)
    |
    v
Main Loop (decides action)
    |
    v
Trader (executes via Jupiter)
    |
    v
Solana Blockchain
```

## Security Considerations

1. **Private Key Protection**

   - Never commit `.env` to version control
   - Restrict file permissions: `chmod 600 .env`
   - Consider using environment variables or secrets management

2. **RPC Endpoint**

   - Use a trusted RPC provider
   - Consider rate limiting and quotas

3. **Position Sizing**

   - Start small and scale gradually
   - Set conservative `MAX_POSITION_SIZE_USDC`

4. **Monitoring**
   - Regularly review logs
   - Set up alerts for errors (future enhancement)

## Performance Optimization

- Use a paid RPC endpoint for better reliability
- Adjust `CHECK_INTERVAL_SECONDS` based on your strategy (lower = more responsive but higher costs)
- Optimize `PRICE_CACHE_SECONDS` to balance freshness vs API calls
- Consider running on a VPS for 24/7 operation with low latency

## Limitations & Future Enhancements

Current limitations:

- Single trading pair (SOL/USDC)
- Spot trading only (no leverage/margin)
- Simple market orders via Jupiter
- No backtesting framework
- No web interface

Potential enhancements:

- Multi-pair support
- Backtesting system
- Web dashboard for monitoring
- Telegram/Discord notifications
- Advanced order types
- Machine learning strategies
- Performance analytics

## Contributing

This is a personal trading bot. If you fork and enhance it, consider:

- Writing tests for new strategies
- Documenting configuration options
- Following the existing code structure
- Using type hints and docstrings

## License

This project is provided as-is for educational and personal use. Use at your own risk.

## Disclaimer

**IMPORTANT**: Trading cryptocurrencies involves substantial risk of loss. This bot is provided for educational purposes. The authors are not responsible for any financial losses incurred through the use of this software. Always test thoroughly on devnet before using real funds. Never invest more than you can afford to lose.

## Support

For issues, questions, or enhancements:

1. Review the logs in `logs/trading_bot.log`
2. Check this README for troubleshooting steps
3. Verify your configuration in `.env`
4. Test on devnet before reporting issues

## Acknowledgments

- Built for trading on [Solana](https://solana.com/)
- Uses [Jupiter](https://jup.ag/) for trade aggregation
- Price data from [CoinGecko](https://www.coingecko.com/) and Jupiter APIs
