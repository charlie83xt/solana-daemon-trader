import requests
import os

class SentimentSignalFetcher:
    def __init__(self):
        # self.helius_api = os.getenv("HELIUS_API_KEY")
        # self.social_sources = ["helius", "coingecko", "mock"]
        self.volume_map = {}


    def cache_volumes(self, token_list):
        # Should be called once per cycle with token data from coingecko
        for token in token_list:
            symbol = token["symbol"]
            vol = token.get("volume24h", 0)
            self.volume_map[symbol] = vol


    def get_onchain_popularity(self, symbol):
        vol = self.volume_map.get(symbol, 0)
        # Normalize volume to 0-1 (relative popularity)
        top_vol = max(self.volume_map.values(), default=1)

        if top_vol == 0:
            return 0.0
            
        return min(vol / top_vol, 1.0)


    def get_social_score(self, symbol: str) -> float:
        # TODO: Later connect to Twitter, Farcaster, or SocialScan
        from token_scanner import fetch_top_tokens
        tokens = fetch_top_tokens()

        # Normalize volumes to [0, 1]
        max_volume = max(t.get("volume24h", 1) for t in tokens)
        for t in tokens:
            if t["symbol"].upper() == symbol.upper():
                return round(t.get("volume24h", 0) / max_volume, 3)
        
        return 0.1 # Fallback low interest score 