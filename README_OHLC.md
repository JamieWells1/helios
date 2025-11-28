# OHLC Data & Technical Indicators

This bot now supports OHLC (Open, High, Low, Close, Volume) candle data for advanced mathematical trading strategies.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Enable OHLC data in .env

```bash
USE_OHLC_DATA=true
OHLC_TIMEFRAME=1h
OHLC_HISTORY_LIMIT=200
```

### 3. Run with RSI strategy

```bash
python example_rsi_bot.py
```

## Features

### Data Sources
- **GeckoTerminal API** (free, no API key required)
- Supports 1700+ DEXs including Solana
- Timeframes: 1m, 5m, 15m, 1h, 4h, 1d

### Technical Indicators
- **RSI** (Relative Strength Index)
- **MACD** (Moving Average Convergence Divergence)
- **Bollinger Bands**
- **EMA/SMA** (Exponential/Simple Moving Averages)

### Data Storage
- SQLite database for persistence
- Automatic backfilling on startup
- Efficient caching

## Architecture

```
src/
├── data/
│   ├── models.py           # Dataclass models for candles
│   ├── ohlc_fetcher.py     # GeckoTerminal API integration
│   └── candle_store.py     # SQLite storage & caching
├── indicators/
│   └── technical.py        # RSI, MACD, Bollinger Bands
└── strategies/
    └── rsi_strategy.py     # Example RSI strategy
```

## Creating Custom Strategies

### Example: RSI Strategy

```python
from src.strategies.rsi_strategy import RSIStrategy, RSIStrategyConfig
from src.main import TradingBot

# Initialize bot
bot = TradingBot()

# Configure strategy
config = RSIStrategyConfig(
    rsi_oversold=30.0,    # Buy when RSI < 30
    rsi_overbought=70.0,  # Sell when RSI > 70
    rsi_period=14
)

strategy = RSIStrategy(bot.config, config)

# Run
bot.initialize(strategy=strategy)
bot.run()
```

### Custom Strategy Template

```python
from dataclasses import dataclass
from src.strategies.base import BaseStrategy
from src.data.models import CandleList
from src.indicators.technical import TechnicalIndicators, IndicatorConfig

@dataclass
class MyStrategyConfig:
    """Your strategy configuration."""
    param1: float = 10.0
    param2: int = 20

class MyStrategy(BaseStrategy):
    """Your custom strategy."""

    def __init__(self, config: dict, strategy_config: MyStrategyConfig):
        super().__init__(config)
        self.strategy_config = strategy_config

        # Initialize indicators
        indicator_config = IndicatorConfig()
        self.indicators = TechnicalIndicators(indicator_config)

    def update(self, current_price: float) -> None:
        pass

    def should_buy(self, current_price: float) -> bool:
        return False

    def should_sell(self, current_price: float) -> bool:
        return False

    def should_buy_candles(self, candles: CandleList) -> bool:
        """Your buy logic using OHLC data."""
        # Calculate indicators
        indicators = self.indicators.calculate_all(candles)

        # Your logic here
        if indicators.rsi < 30 and candles.latest.close < indicators.bb_lower:
            return True

        return False

    def should_sell_candles(self, candles: CandleList) -> bool:
        """Your sell logic using OHLC data."""
        indicators = self.indicators.calculate_all(candles)

        if indicators.rsi > 70:
            return True

        return False
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_OHLC_DATA` | false | Enable OHLC data fetching |
| `OHLC_TIMEFRAME` | 1h | Candle timeframe (1m, 5m, 15m, 1h, 4h, 1d) |
| `OHLC_HISTORY_LIMIT` | 200 | Number of historical candles to maintain |

### Supported Timeframes

- `1m` - 1 minute candles
- `5m` - 5 minute candles
- `15m` - 15 minute candles
- `1h` - 1 hour candles (recommended for intraday)
- `4h` - 4 hour candles
- `1d` - Daily candles

## Technical Indicators

### Using Indicators

```python
from src.indicators.technical import TechnicalIndicators, IndicatorConfig
from src.data.candle_store import CandleStore, StoreConfig

# Initialize
config = IndicatorConfig(
    rsi_period=14,
    macd_fast=12,
    macd_slow=26,
    bb_period=20
)
indicators = TechnicalIndicators(config)

# Get candles
store = CandleStore(StoreConfig(auto_discover_pool=True))
candles = store.get_candles('1h', 200)

# Calculate all indicators
values = indicators.calculate_all(candles)

print(f"RSI: {values.rsi:.2f}")
print(f"MACD: {values.macd_line:.2f}")
print(f"BB Upper: {values.bb_upper:.2f}")
```

### Individual Indicators

```python
# RSI only
rsi = indicators.calculate_rsi(candles)

# Simple moving average
sma = indicators.calculate_sma(candles.closes, period=20)

# Exponential moving average
ema = indicators.calculate_ema(candles.closes, period=12)
```

## Data Models

All data uses strongly-typed dataclasses (no messy dictionaries):

```python
@dataclass
class Candle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass
class CandleList:
    candles: List[Candle]
    timeframe: str

    @property
    def latest(self) -> Candle

    @property
    def closes(self) -> List[float]

@dataclass
class IndicatorValues:
    rsi: float
    macd_line: float
    macd_signal: float
    macd_histogram: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
```

## Performance

- SQLite database stores all historical candles
- In-memory caching for frequently accessed data
- Efficient bulk updates
- Minimal API calls (data persists across restarts)

## Troubleshooting

### "Could not auto-discover SOL/USDC pool"
The bot automatically finds the most liquid SOL/USDC pool. If this fails:
1. Check your internet connection
2. Try again (API might be temporarily unavailable)
3. Manually specify pool address in code

### "Insufficient candles"
Strategies require minimum historical data:
- RSI: 14+ candles (by default)
- MACD: 35+ candles
- Bollinger Bands: 20+ candles

Increase `OHLC_HISTORY_LIMIT` if needed.

### Database errors
Delete the database to reset:
```bash
rm data/candles.db
```

## Testing

Test OHLC fetching without trading:

```python
from src.data.candle_store import CandleStore, StoreConfig

store = CandleStore(StoreConfig(auto_discover_pool=True))
store.backfill('1h', 100)
candles = store.get_candles('1h', 50)

print(f"Fetched {len(candles)} candles")
print(f"Latest: {candles.latest}")
```

## Limitations

- Single timeframe per bot instance
- GeckoTerminal API has no official rate limits but be respectful
- Historical data limited by API (typically 1000 candles max)
- No tick data or order book depth

## Next Steps

1. Implement your custom strategy
2. Backtest using historical data
3. Test on small position sizes
4. Monitor and iterate

See `example_rsi_bot.py` for a complete working example.
