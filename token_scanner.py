import requests


def fetch_top_tokens(limit=20):
    """
    Fetch top sSolana tokens by volume from Jupoiter API
    """

    try:
        url = f"https://cache.jup.ag/tokens"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        tokens = res.json()

        # Filter for Solana-native tokens with USDC pairs
        filtered = [t for t in tokens if t.get("extensions", {}).get("coingeckoId") and t.get("symbol") != "USDC"]

        # Sort by market cap or volume if available
        sorted_tokens = sorted(filtered, key=lambda x: x.get("volume24h", 0), reverse=True)
        return sorted_tokens[:limit]

    except Exception as e:
        print(f"[TokenScanner] Error fetching top tokens: {e}")
        return [{"symbol": "SOL", "address": "So11111111111111111111111111111111111111112"}]





