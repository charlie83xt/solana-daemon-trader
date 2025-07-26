# Extension for TraderOrchestrator to support multi-token evaluation
import asyncio
from token_scanner import fetch_top_tokens
from jupiter_swapper import JupiterSwapper
# from gdrive_logger import DriveLogger
from token_performance import TokenPerformanceTracker
from sentiment_fetcher import SentimentSignalFetcher
# from log_paths import get_log_path
from real_market_data import RealMarketDataFetcher
# from log_router import LogRouter


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
        # self.logger = LogRouter(use_drive = True)

    async def evaluate_token(self, token):
        symbol = token["symbol"]
        print(f"[MultiTokenTrader] Evaluating {symbol}...")

        price_data = self.market_fetcher.fetch_price_history(symbol)
        if not price_data or len(price_data) < 50:
            print(f"[MultiTokenTrader] Skipping {symbol} due to limited price history.")

        indicators = self.indicator.compute_indicators(price_data)
        if not indicators:
            return None
        indicators['symbol'] = symbol

        decision = await self.agent_ensemble.resolve_decision(indicators)

        if decision["confidence"] is None or decision["amount"] is None:
            raise ValueError(f"Agent returned incomplete action decision: {decision}")

        decision["confidence"] = float(decision["confidence"])

        # Inject sentiment
        social = self.signal_fetcher.get_social_score(symbol)
        # onchain = self.signal_fetcher.get_onchain_popularity(token["address"])
        onchain = self.signal_fetcher.get_onchain_popularity(symbol)
        combined = 0.5 * social + 0.5 * onchain
        combined = max(min(combined, 1), -0.9)

        old_conf = decision["confidence"]
        decision["confidence"] *= (1 + combined)
        decision["confidence"] = max(decision["confidence"], 0.01)

        print(f"[MultiTokenTrader] Sentiment-adjusted confidence for {symbol}: {decision['confidence']:.2f} (was {old_conf:.2f}, combined={combined:.2f})")

        return decision, indicators, combined


    async def evaluate_and_trade_top_tokens(self):
        tokens = fetch_top_tokens(limit=10)
        if not tokens:
            print(f"[MultiTokenTrader] No tokens candidates from trade history.")
            return False


        preferred_symbols = self.performance_tracker.top_tokens_by_pnl()
        if not preferred_symbols:
            print(f"[MultiTokenTrader] No preferred symbols found. Falling back to ['SOL'].")
            preferred_symbols = ['SOL']

        tokens = [t for t in tokens if t["symbol"] in preferred_symbols]
        print(f"[MultiTokenTrader] Selected top tokens: {preferred_symbols}")


        best_decision = {"confidence": 0.0}
        best_token = None
        best_indicators = None
        best_combined = 0.0

        self.signal_fetcher.cache_volumes(tokens)


        for token in tokens:
            # symbol = token["symbol"]
            # print(f"[MultiTokenTrader] Evaluating {symbol}...")
            try:
                result = await self.evaluate_token(token)
                if not result:
                    continue
                decision, indicators, combined = result

                # price_data = self.market_fetcher.fetch_price_history(symbol)
                # if not price_data or len(price_data) < 50:
                #     print(f"[MultiTokenTrader] Skipping {symbol} due to limited price history.")
                #     continue


                # indicators = self.indicator.compute_indicators(price_data)
                # if not indicators:
                #     continue
                # indicators['symbol'] = symbol
                # decision = await self.agent_ensemble.resolve_decision(indicators)

                # if decision["confidence"] is None or decision["amount"] is None:
                #     raise ValueError(f"Agent returned incomplete action decision: {decision}")

                # # Inject sentiment
                # social = self.signal_fetcher.get_social_score(symbol)
                # onchain = self.signal_fetcher.get_onchain_popularity(token["address"])
                # combined = 0.5 * social + 0.5 * onchain
                # decision["confidence"] *= (1 + combined)


                # print(f"[MultiTokenTrader] Sentiment-adjusted confidence for {symbol}: {decision['confidence']:.2f}")


                if decision["confidence"] > best_decision["confidence"]:
                    best_decision = decision
                    best_token = token
                    best_indicators = indicators
                    best_combined = combined
                    
            except Exception as e:
                print(f"[MultiTokenTrader] Error evaluating {token['symbol']}: {e}")


        # ✅ Fallback if nothing selected
        # if not best_token:
        #     print("[MultiTokenTrader] No good token candidates from trade history, falling back to top 5 tokens...")
        #     fallback_tokens = fetch_top_tokens(limit=5)
        #     for token in fallback_tokens:
        #         symbol = token["symbol"]
        #         try:
        #             print(f"[MultiTokenTrader] [Fallback] Evaluating {symbol}...")
        #             price_data = self.market_fetcher.fetch_price_history(symbol)
        #             if not price_data or len(price_data) < 50:
        #                 continue


        #             indicators = self.indicator.compute_indicators(price_data)
        #             if not indicators:
        #                 continue
        #             indicators['symbol'] = symbol
        #             decision = await self.agent_ensemble.resolve_decision(indicators)


        #             social = self.signal_fetcher.get_social_score(symbol)
        #             onchain = self.signal_fetcher.get_onchain_popularity(token["address"])
        #             combined = 0.5 * social + 0.5 * onchain
        #             combined = max(min(combined, 1), -0.9)

        #             old_conf = decision["confidence"]
        #             decision["confidence"] *= (1 + combined)
        #             decision["confidence"] = max(decision["confidence"], 0.01)
        #             print(f"[MultiTokenTrader] Sentiment-adjusted confidence for {symbol}: {decision['confidence']:.2f} (was {old_conf:.2f}, combined={combined:.2f})")


        #             if decision["confidence"] > best_decision["confidence"]:
        #                 best_decision = decision
        #                 best_token = token
        #                 best_indicators = indicators
        #         except Exception as e:
        #             print(f"[MultiTokenTrader] Fallback evaluation failed for {symbol}: {e}")


        if best_token and self.risk.approve_trade(best_decision, best_indicators):
            print(f"[MultiTokenTrader] Best decision {best_decision} for {best_token['symbol']}")
            try:
                tx_sig = await self.swapper.execute_swap(best_token, best_decision)
            except Exception as e:
                print(f"[MultiTokenTrader] Swap failed: {e}")
                tx_sig = "-"


            # ✅ Log trade fully
            self.risk.log_trade(
                best_decision["action"],
                best_decision["amount"],
                best_decision["price"],
                best_decision.get("confidence", 1.0),
                best_indicators.get("symbol", "UNKNOWN"),
                tx_sig,
                best_combined
            )
            # DriveLogger().upload_or_append("logs/trade_log.csv")
            return True


        print(f"[MultiTokenTrader] Not valid trade executed.")
        return False


    # async def evaluate_and_trade_top_tokens(self):
    #     tokens = fetch_top_tokens(limit=10)

    #     if not tokens:
    #         print(f"[MultiTokenTrader] No tokens found.")
    #         return

    #     preferred_symbols = self.performance_tracker.top_tokens_by_pnl()
    #     tokens = [t for t in tokens if t["symbol"] in preferred_symbols]
    #     print(f"[MultiTokenTrader] Selected top tokens: {preferred_symbols}")

    #     best_decision = {"confidence": 0.0}
    #     best_token = None
    #     best_indicators = None
    #     combined_sentiment = 0.0

    #     self.signal_fetcher.cache_volumes(tokens)

    #     for token in tokens:
    #         symbol = token['symbol']
    #         print(f"[MultiTokenTrader] Evaluating {symbol}...")
    #         try:
    #             price_data = self.market_fetcher.fetch_price_history(symbol)
    #             if not price_data or len(price_data) < 50:
    #                 print(f"[MultiTokenTrader] Skipping {symbol} due to limited price history.")
    #                 continue
                
    #             current_price = price_data[-1]
    #             indicators = self.indicator.compute_indicators(price_data)
    #             indicators['symbol'] = symbol

    #             decision = await self.agent_ensemble.resolve_decision(indicators)
    #             decision["price"] = current_price

    #             # Injecting sentiment Boost
    #             social = self.signal_fetcher.get_social_score(symbol)
    #             onchain = self.signal_fetcher.get_onchain_popularity(token.get("address"))
    #             combined_sentiment = 0.5 * social + 0.5 * onchain
    #             decision["confidence"] *= (1 + combined_sentiment)

    #             print(f"[MultiTokenTrader] Sentiment-adjusted confidence for {symbol}: {decision['confidence']:.2f}")

    #             if decision["confidence"] > best_decision["confidence"]:
    #                 best_decision = decision
    #                 best_token = token
    #                 best_indicators = indicators
    #         except Exception as e:
    #             print(f"[MultiTokenTrader] Error evaluating {symbol}: {e}")

    #     if best_token and self.risk.approve_trade(best_decision, best_indicators):
    #         print(f"[MultiTokenTrader] Best decision {best_decision} for {best_token['symbol']}")

    #         try:
    #             tx_sig = await self.swapper.execute_swap(best_token, best_decision)
    #         except Exception as e:
    #             print(f"[MultiTokenTrader] Swap failed: {e}")
    #             tx_sig = "-"

    #         self.risk.log_trade(
    #             best_decision["action"],
    #             best_decision["amount"],
    #             best_decision["price"],
    #             best_decision.get("confidence", 1.0),
    #             best_indicators.get("symbol", "UNKNOWN"),
    #             tx_sig,
    #             combined_sentiment
    #         )
    #         return true
    #         # try:
    #         #     DriveLogger().upload_or_append("logs/trade_log.csv")
    #         # except Exception as e:
    #         #     print(f"[MultiTokenTrader] Failed to upload trade log: {e}")
    #     else:
    #         print(f"[MultiTokenTrader] Not valid trade executed.")
    #         return False
    

    def execute_jupiter_swap(self, token, decision):
        print(f"[JupiterSwap] Simulating {decision['action']} {decision['amount']} of {token['symbol']} (stub)")
