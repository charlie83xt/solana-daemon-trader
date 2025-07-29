import requests
import os

class SentimentSignalFetcher:
    def __init__(self):
        # self.helius_api = os.getenv("HELIUS_API_KEY")
        # self.social_sources = ["helius", "coingecko", "mock"]
        self.volume_map = {}


    def cache_volumes(self, token_list):
        self.volume_map = {}
        # Should be called once per cycle with token data from coingecko
        for token in token_list:
            symbol = token["symbol"]
            vol = token.get("volume24h", 0)
            self.volume_map[symbol] = vol
        print(f"[SentimentFetcher] Cached volumes for {len(self.volume_map)} tokens: {list(self.volume_map.items())[:3]}")


    def get_onchain_popularity(self, symbol):
        # Defensive avoidance max() on empty
        if not self.volume_map:
            print(f"[SentimentFetcher] Empty volume map. Returning 0 for {symbol}")
            return 0.0

        # Normalize volume to 0-1 (relative popularity)
        vol = self.volume_map.get(symbol, 0)
        top_vol = max(self.volume_map.values(), default=1)

        # print(f"[SentimentFetcher] Popularity check: symbol={symbol}, vol={vol} top_vol={top_vol}")

        if top_vol <= 0:
            print(f"[SentimentFetcher] top_vol={top_vol}! Avoiding division for {symbol}")
            return 0.0
        
        try:
            ratio = vol / top_vol
            return min(ratio, 1.0)
        except ZeroDivisionError:
            print(f"[SentimentFetcher] ZeroDivisionError for {symbol} -- vol={vol}, top_vol={top_vol} ")
            return 0.0


    def get_social_score(self, symbol: str) -> float:
        # TODO: Later connect to Twitter, Farcaster, or SocialScan
        from token_scanner import fetch_top_tokens
        tokens = fetch_top_tokens()
        
        if not tokens:
            print(f"[SentimentFetcher] Empty token list.Returning default score for {symbol}")
            return 0.1

        # Normalize volumes to [0, 1]
        volumes = [t.get("volume24h", 0) for t in tokens]
        max_volume = max(volumes, default=1)

        if max_volume <= 0:
            print(f"[SentimentFetcher] max_volume=0 for {symbol}. Avoiding division.")
            return 0.1

        for t in tokens:
            if t["symbol"].upper() == symbol.upper():
                return round(t.get("volume24h", 0) / max_volume, 3)
        
        return 0.1 # Fallback low interest score 