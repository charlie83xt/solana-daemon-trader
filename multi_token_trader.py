# Extension for TraderOrchestrator to support multi-token evaluation
import asyncio
from token_scanner import fetch_top_tokens
from jupiter_swapper import JupiterSwapper
from gdrive_logger import DriveLogger
from token_performance import TokenPerformanceTracker
from sentiment_fetcher import SentimentSignalFetcher
from log_paths import get_log_path
from real_market_data import RealMarketDataFetcher
from log_router import LogRouter


class MultiTokenTrader:
    def __init__(self, market_fetcher, indicator, agent_ensemble, risk, keypair): #Before: (self, market_fetcher, indicator, agent_ensemble, risk, executor)
        self.market_fetcher = market_fetcher
        self.indicator = indicator
        self.agent_ensemble = agent_ensemble
        self.risk = risk
        self.keypair = keypair
        self.swapper = JupiterSwapper(self.keypair)

        self.performance_tracker = TokenPerformanceTracker()
        self.signal_fetcher = SentimentSignalFetcher()
        self.logger = LogRouter(use_drive = True)

    
    async def evaluate_and_trade_top_tokens(self):
        tokens = fetch_top_tokens(limit=10)

        if not tokens:
            print(f"[MultiTokenTrader] No tokens found.")
            return

        preferred_symbols = self.performance_tracker.top_tokens_by_pnl()
        tokens = [t for t in tokens if t["symbol"] in preferred_symbols]
        print(f"[MultiTokenTrader] Selected top tokens: {preferred_symbols}")

        best_decision = {"confidence": 0.0}
        best_token = None
        best_indicators = None
        self.signal_fetcher.cache_volumes(tokens)

        for token in tokens:
            print(f"[MultiTokenTrader] Evaluating {token['symbol']}...")
            try:
                price_data = self.market_fetcher.fetch_price_history(token['symbol'])
                if not price_data or len(price_data) < 50:
                    continue

                indicators = self.indicator.compute_indicators(price_data)
                indicators['symbol'] = token['symbol']
                decision = await self.agent_ensemble.resolve_decision(indicators)

                # Injecting sentiment Boost
                social = self.signal_fetcher.get_social_score(token["symbol"])
                onchain = self.signal_fetcher.get_onchain_popularity(token["address"])
                combined = 0.5 * social + 0.5 * onchain
                decision["confidence"] *= (1 + combined)

                print(f"[MultiTokenTrader] Sentiment-adjusted confidence for {token['symbol']}: {decision['confidence']:.2f}")

                if decision["confidence"] > best_decision["confidence"]:
                    best_decision = decision
                    best_token = token
                    best_indicators = indicators
            except Exception as e:
                print(f"[MultiTokenTrader] Error evaluating {token['symbol']}: {e}")

        if best_token and self.risk.approve_trade(best_decision, best_indicators):
            print(f"[MultiTokenTrader] Best decision {best_decision} for {best_token['symbol']}")                
            # self.execute_jupiter_swap(best_token, best_decision)
            try:
                tx_sig = await self.swapper.execute_swap(best_token, best_decision)
            except Exception as e:
                print(f"[MultiTokenTrader] Swap failed: {e}")
                tx_sig = "-"
            self.risk.log_trade(
                best_decision["action"],
                best_decision["amount"],
                best_decision["price"],
                best_decision.get("confidence", 1.0),
                best_indicators.get("symbol", "UNKNOWN"),
                tx_sig,
                combined
            )
            try:
                DriveLogger().upload_or_append("logs/trade_log.csv")
            except Exception as e:
                print(f"[MultiTokenTrader] Failed to upload trade log: {e}")
        else:
            print(f"[MultiTokenTrader] Not valid trade executed.")
    

    def execute_jupiter_swap(self, token, decision):
        print(f"[JupiterSwap] Simulating {decision['action']} {decision['amount']} of {token['symbol']} (stub)")
