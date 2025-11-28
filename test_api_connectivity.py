"""
Quick test to verify GeckoTerminal API connectivity.
"""

import requests
import time


def test_geckoterminal():
    """Test if GeckoTerminal API is accessible."""

    print("Testing GeckoTerminal API connectivity...")
    print("-" * 60)

    url = "https://api.geckoterminal.com/api/v2/networks/solana/tokens/So11111111111111111111111111111111111111112/pools"

    print(f"Making request to: {url}")
    print("Waiting for response...")

    start = time.time()

    try:
        response = requests.get(url, params={'page': 1}, timeout=10)
        elapsed = time.time() - start

        print(f"✓ Response received in {elapsed:.2f} seconds")
        print(f"✓ Status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            pools = data.get('data', [])
            print(f"✓ Found {len(pools)} pools")

            # Look for SOL/USDC
            for pool in pools[:5]:  # Check first 5
                name = pool.get('attributes', {}).get('name', '')
                if 'USDC' in name.upper():
                    print(f"✓ Found pool: {name}")
                    address = pool.get('attributes', {}).get('address')
                    print(f"  Address: {address}")
                    break

            return True
        else:
            print(f"✗ Unexpected status code: {response.status_code}")
            return False

    except requests.Timeout:
        elapsed = time.time() - start
        print(f"✗ Request timed out after {elapsed:.2f} seconds")
        return False
    except requests.RequestException as e:
        elapsed = time.time() - start
        print(f"✗ Request failed after {elapsed:.2f} seconds: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


if __name__ == '__main__':
    success = test_geckoterminal()
    print("-" * 60)

    if success:
        print("✓ GeckoTerminal API is accessible")
        print("You can proceed with running the bot.")
    else:
        print("✗ Cannot reach GeckoTerminal API")
        print("Check your internet connection or try again later.")

    exit(0 if success else 1)
