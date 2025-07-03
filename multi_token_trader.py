# Extension for TraderOrchestrator to support multi-token evaluation
import asyncio
from token_scanner import fetch_top_tokens
from jupiter_swapper import JupiterSwapper
from gdrive_logger import DriveLogger

class MultiTokenTrader:
    def __init__(self, market_fetcher, indicator, agent_ensemble, risk, executor):
        self.market_fetcher = market_fetcher
        self.indicator = indicator
        self.agent_ensemble = agent_ensemble
        self.risk = risk
        self.executor = executor
        self.swapper = JupiterSwapper(self.executor)

    
    async def evaluate_and_trade_top_tokens(self):
        tokens = fetch_top_tokens(limit=3)
        if not tokens:
            print(f"[MultiTokenTrader] No tokens found.")
            return

        best_decision = {"confidence": 0.0}
        best_token = None
        best_indicators = None

        for token in tokens:
            print(f"[MultiTokenTrader] Evaluating {token['symbol']}...")
            try:
                price_data = self.market_fetcher.fetch_price_history(token['symbol'])
                if not price_data or len(price_data) < 50:
                    continue

                indicators = self.indicator.compute_indicators(price_data)
                indicators['symbol'] = token['symbol']
                decision = await self.agent_ensemble.resolve_decision(indicators)

                if decision["confidence"] > best_decision["confidence"]:
                    best_decision = decision
                    best_token = token
                    best_indicators = indicators
            except Exception as e:
                print(f"[MultiTokenTrader] Error evaluating {token['symbol']}: {e}")

        if best_token and self.risk.approve_trade(best_decision, best_indicators):
            print(f"[MultiTokenTrader] Best decision {best_decision} for {best_token["symbol"]}")                
            # self.execute_jupiter_swap(best_token, best_decision)
            tx_sig = await self.swapper.execute_swap(best_token, best_decision)
            self.risk.log_trade(
                best_decision["action"],
                best_decision["amount"],
                best_decision["price"],
                best_decision.get("confidence", 1.0),
                best_indicators.get("symbol", "UNKNOWN"),
                tx_sig
            )
            DriveLogger().upload_or_append("logs/trade_log.csv")
        else:
            print(f"[MultiTokenTrader] Not valid trade executed.")
    

    def execute_jupiter_swap(self, token, decision):
        print(f"[JupiterSwap] Simulating {decision["action"]} {decision["amount"]} of {token["symbol"]} (stub)")
