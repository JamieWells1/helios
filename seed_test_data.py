"""
Generate synthetic OHLC data for testing when APIs are blocked.

Creates realistic SOL/USDC price data with trends, volatility, and patterns.
This lets you develop and backtest your strategy without needing API access.

Usage:
    python3 seed_test_data.py --candles 10000
"""

import argparse
import random
import time
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

import numpy as np


def generate_realistic_ohlc(num_candles=10000, base_price=140.0, timeframe_seconds=60):
    """
    Generate realistic OHLC data with trends, volatility, and mean reversion.

    Args:
        num_candles: Number of candles to generate
        base_price: Starting price
        timeframe_seconds: Seconds per candle (60 = 1 minute)

    Returns:
        List of (timestamp, open, high, low, close, volume) tuples
    """
    print(f"Generating {num_candles} candles of synthetic SOL/USDC data...")

    candles = []
    current_time = int(time.time()) - (num_candles * timeframe_seconds)
    current_price = base_price

    # Generate multi-scale trends
    trend = 0.0  # Overall trend direction
    volatility = 0.02  # Price volatility (2%)

    for i in range(num_candles):
        # Add some macro trends (changes every ~100 candles)
        if i % 100 == 0:
            trend = random.uniform(-0.001, 0.001)  # -0.1% to +0.1% trend per candle

        # Add volatility variation
        if i % 50 == 0:
            volatility = random.uniform(0.01, 0.03)  # 1% to 3% volatility

        # Generate price movement
        price_change = current_price * (trend + random.gauss(0, volatility))
        next_price = current_price + price_change

        # Ensure price stays positive and somewhat realistic
        next_price = max(next_price, base_price * 0.5)
        next_price = min(next_price, base_price * 2.0)

        # Generate OHLC for this candle
        open_price = current_price
        close_price = next_price

        # High and low with some randomness
        high_price = max(open_price, close_price) * random.uniform(1.0, 1.01)
        low_price = min(open_price, close_price) * random.uniform(0.99, 1.0)

        # Generate realistic volume (higher during volatile periods)
        base_volume = 1000000
        volume = base_volume * random.uniform(0.5, 2.0) * (1 + abs(price_change) * 10)

        candles.append({
            'timestamp': current_time,
            'open': round(open_price, 4),
            'high': round(high_price, 4),
            'low': round(low_price, 4),
            'close': round(close_price, 4),
            'volume': round(volume, 2)
        })

        current_price = next_price
        current_time += timeframe_seconds

        if (i + 1) % 1000 == 0:
            print(f"  Generated {i + 1}/{num_candles} candles...")

    print(f"✓ Generated {num_candles} candles")
    print(f"  Price range: ${min(c['low'] for c in candles):.2f} - ${max(c['high'] for c in candles):.2f}")
    print(f"  Start: ${candles[0]['close']:.2f}, End: ${candles[-1]['close']:.2f}")

    return candles


def insert_candles_to_db(candles, timeframe='1m', db_path='data/candles.db'):
    """
    Insert candles into the database.

    Args:
        candles: List of candle dictionaries
        timeframe: Timeframe string (e.g., '1m')
        db_path: Path to SQLite database
    """
    print(f"\nInserting {len(candles)} candles into database...")

    # Create data directory if needed
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candles (
            timeframe TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL NOT NULL,
            PRIMARY KEY (timeframe, timestamp)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timeframe_timestamp
        ON candles(timeframe, timestamp DESC)
    """)

    # Insert candles
    for candle in candles:
        cursor.execute("""
            INSERT OR REPLACE INTO candles
            (timeframe, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            timeframe,
            candle['timestamp'],
            candle['open'],
            candle['high'],
            candle['low'],
            candle['close'],
            candle['volume']
        ))

    conn.commit()

    # Verify
    cursor.execute("""
        SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
        FROM candles
        WHERE timeframe = ?
    """, (timeframe,))

    count, min_ts, max_ts = cursor.fetchone()

    print(f"✓ Successfully inserted {count} candles into database")
    print(f"  Timeframe: {timeframe}")
    print(f"  Date range: {datetime.fromtimestamp(min_ts)} to {datetime.fromtimestamp(max_ts)}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description='Generate synthetic OHLC test data')
    parser.add_argument('--candles', type=int, default=10000, help='Number of candles to generate (default: 10000)')
    parser.add_argument('--base-price', type=float, default=140.0, help='Base price for SOL/USDC (default: 140.0)')
    parser.add_argument('--timeframe', type=str, default='1m', help='Timeframe (default: 1m)')
    parser.add_argument('--db', type=str, default='data/candles.db', help='Database path (default: data/candles.db)')
    args = parser.parse_args()

    print("=" * 60)
    print("SYNTHETIC DATA GENERATOR")
    print("=" * 60)
    print(f"Generating {args.candles} {args.timeframe} candles")
    print(f"Base price: ${args.base_price}")
    print(f"Database: {args.db}")
    print("=" * 60)
    print()

    # Generate candles
    candles = generate_realistic_ohlc(
        num_candles=args.candles,
        base_price=args.base_price,
        timeframe_seconds=60  # 1 minute
    )

    # Insert into database
    insert_candles_to_db(candles, timeframe=args.timeframe, db_path=args.db)

    print()
    print("=" * 60)
    print("DONE!")
    print("=" * 60)
    print("You can now run backtests:")
    print(f"  python3 main.py --test --candles {args.candles}")
    print()
    print("Note: This is SYNTHETIC data for testing purposes.")
    print("=" * 60)


if __name__ == '__main__':
    main()
