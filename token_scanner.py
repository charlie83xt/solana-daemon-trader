import requests


def fetch_top_tokens(limit=20):
    """
    Fetch top sSolana tokens by volume from Jupoiter API
    """

    try:
        url = f"https://cache.jup.ag/tokens"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        

        # Trimming and parsing memory footprint
        tokens = res.json()
        filtered = []
        # Filter for Solana-native tokens with USDC pairs
        # filtered = [t for t in tokens if t.get("extensions", {}).get("coingeckoId") and t.get("symbol") != "USDC"]
        for t in tokens:
            if (
                t.get("extensions", {}).get("coingeckoId") and 
                t.get("symbol") != "USDC"
                ):
                filtered.append({
                    "symbol": t.get("symbol"),
                    "address": t.get("address"),
                    "volume24h": t.get("volume24h", 0),
                })

        # Sort by market cap or volume if available
        sorted_tokens = sorted(filtered, key=lambda x: x["volume24h"], reverse=True)
        return sorted_tokens[:limit]

    except Exception as e:
        print(f"[TokenScanner] Error fetching top tokens: {e}")
        return [{"symbol": "SOL", "address": "So11111111111111111111111111111111111111112"}]





