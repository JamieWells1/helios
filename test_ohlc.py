"""
Quick test script to verify OHLC data fetching works.

Run this before using the full trading bot to ensure everything is set up correctly.
"""

from src.data.candle_store import CandleStore, StoreConfig
from src.indicators.technical import TechnicalIndicators, IndicatorConfig


def test_ohlc_fetching():
    """Test OHLC data fetching and indicators."""

    print("=" * 60)
    print("Testing OHLC Data System")
    print("=" * 60)

    # Initialize candle store
    print("\n1. Initializing candle store...")
    config = StoreConfig(
        db_path="data/test_candles.db",
        auto_discover_pool=True
    )

    try:
        store = CandleStore(config)
        print(f"✓ Pool discovered: {store.pool_address[:16]}...")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return False

    # Fetch some candles
    print("\n2. Fetching 50 1-hour candles...")
    try:
        store.backfill('1h', 50)
        candles = store.get_candles('1h', 50)
        print(f"✓ Fetched {len(candles)} candles")
        print(f"   Latest: {candles.latest}")
    except Exception as e:
        print(f"✗ Failed to fetch candles: {e}")
        return False

    # Calculate indicators
    print("\n3. Calculating technical indicators...")
    try:
        indicator_config = IndicatorConfig(
            rsi_period=14,
            macd_fast=12,
            macd_slow=26,
            bb_period=20
        )
        indicators = TechnicalIndicators(indicator_config)

        values = indicators.calculate_all(candles)

        print(f"✓ RSI: {values.rsi:.2f}")
        print(f"✓ MACD: {values.macd_line:.4f}")
        print(f"✓ BB Upper: ${values.bb_upper:.2f}")
        print(f"✓ BB Middle: ${values.bb_middle:.2f}")
        print(f"✓ BB Lower: ${values.bb_lower:.2f}")

    except Exception as e:
        print(f"✗ Failed to calculate indicators: {e}")
        return False

    # Test individual indicators
    print("\n4. Testing individual indicators...")
    try:
        rsi = indicators.calculate_rsi(candles)
        sma = indicators.calculate_sma(candles.closes, 20)
        ema = indicators.calculate_ema(candles.closes, 12)

        print(f"✓ RSI: {rsi:.2f}")
        print(f"✓ SMA(20): ${sma:.2f}")
        print(f"✓ EMA(12): ${ema:.2f}")

    except Exception as e:
        print(f"✗ Failed individual indicators: {e}")
        return False

    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    print("\nYou can now:")
    print("1. Set USE_OHLC_DATA=true in .env")
    print("2. Run: python example_rsi_bot.py")
    print("=" * 60)

    return True


if __name__ == '__main__':
    success = test_ohlc_fetching()
    exit(0 if success else 1)
