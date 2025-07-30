import requests


def fetch_top_tokens(limit=10):
    """
    Efficiently fetch top Solana tokens by volume from Jupiter API
    """

    try:
        url = "https://raw.githubusercontent.com/charlie83xt/updating_tokens/refs/heads/main/filtered_tokens.json"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        

        # Trimming and parsing memory footprint
        tokens = res.json()
        # filtered = []
        # count = 0

        # # Filter for Solana-native tokens with USDC pairs
        # # filtered = [t for t in tokens if t.get("extensions", {}).get("coingeckoId") and t.get("symbol") != "USDC"]
        # for t in tokens:
        #     if (
        #         t.get("extensions", {}).get("coingeckoId") and 
        #         t.get("symbol") != "USDC"
        #         ):
        #         filtered.append({
        #             "symbol": t.get("symbol"),
        #             "address": t.get("address"),
        #             "volume24h": t.get("volume24h", 0),
        #         })
        #         count += 1

        #     if count >= limit * 3:
        #         break

        # # Sort by market cap or volume if available
        # sorted_tokens = sorted(filtered, key=lambda x: x["volume24h"], reverse=True)
        # top_tokens = sorted_tokens[:limit]
        print(f"[TokenScanner] Returning top {len(tokens[:limit])} tokens")
        return tokens[:limit]

    except Exception as e:
        print(f"[TokenScanner] Error fetching top tokens: {e}")
        return [
            {
                "symbol": "SOL",
                "address": "So11111111111111111111111111111111111111112",
                "volume24h": 1000000
            }
        ]





