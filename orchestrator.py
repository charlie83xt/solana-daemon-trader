import os
import asyncio
import json
from dotenv import load_dotenv
# from solana_data_extractor_adjusted import SolanaDataExtractor
from external_indicator_calculator import IndicatorCalculator
from external_ai_agent_decision import AIAgentCaller
from risk_manager import RiskManager
from executor import TransactionExecutor
from real_market_data import RealMarketDataFetcher
from agents.openai_agent import OpenAIAgent
from agents.rule_based_agent import RuleBasedAgent
from agents.threshold_agent import ThresholdAgent
from agents.agent_orchestrator import AgentOrchestrator
from multi_token_trader import MultiTokenTrader
import traceback
from solders.keypair import Keypair


class TraderOrchestrator:
    def __init__(self):
        load_dotenv(override=True)

        key_json = json.loads(os.getenv("PRIVATE_KEY_JSON"))
        self.keypair = Keypair.from_bytes(key_json)

        self.rpc_url = os.getenv("SOLANA_RPC_URL")
        self.max_position = float(os.getenv("MAX_POSITION_SIZE", 0.1))
        self.max_daily_loss = float(os.getenv("MAX_DAILY_LOSS", 1.0))

        self.market_fetcher = RealMarketDataFetcher()
        self.indicator = IndicatorCalculator()
        self.ai_agent = AIAgentCaller()
        
        self.risk = RiskManager(
            cooldown_minutes = int(os.getenv("COOLDOWN_MINUTES", 10))
        )

        self.agent_ensemble = AgentOrchestrator([
            # OpenAIAgent(),
            ThresholdAgent(),
            # More agents can be added here later
            RuleBasedAgent()
        ])

    async def run_cycle(self):
        try:
            # 1) Get price history
            price_list = self.market_fetcher.fetch_price_history("SOL")
            # 2) Compute indicators
            if not price_list or len(price_list) < 50:
                print("[Orchestrator] Insufficient price history for SOL. Skipping cycle.")
                return False

            indicators = self.indicator.compute_indicators(price_list)
            if not indicators:
                print("[Orchestrator] Marklet data unavailable. Skipping cycle.")
                return False

            # 3) Get AI decision
            decision = await self.agent_ensemble.resolve_decision(indicators)
            if decision["action"] == "HOLD":
                print(f"[Orchestrator] All agents voted HOLD or lacked confidence.")
            # decision = {
            #     "action": "SELL",
            #     "amount": 0.05,
            #     "confidence": 0.95
            # }
            # print(f"[Final Decision] {decision['action']} {decision['amount']} SOL @ confidence {decision['confidence'] * 100:.1f}%")

            if not self.risk.approve_trade(decision, indicators):
                print("[Orchestrator] RiskManager blocked this trade.")
                return False

            # 4) Act on decision
            action = decision.get('action', 'HOLD')
            amount = float(decision.get('amount', 0))

            if action == 'BUY':
                amount = min(self.max_position, amount)
                print(f"[Orchestrator] Decided to BUY {amount} SOL")
                # self.executor.execute_trade('BUY', amount)

            elif action == 'SELL':
                amount = min(self.max_position, amount)
                print(f"[Orchestrator] Decided to SELL {amount} SOL")
                # self.executor.execute_trade('SELL', amount)

            else:
                print("[Orchestrator] No action taken this cycle.")

            self.risk.log_trade(
                action, 
                amount, 
                indicators["price"], 
                decision.get("confidence", 1.0), 
                indicators.get("symbol", 'SOL'), 
                "-", 
                None
            )

        except Exception as e:
            print(f"[Orchestrator] Error during run_cycle: {e}")
            print(f"[Runner] Error during run_cycle().")
            print(f"Type: {type(e)}")
            print(f"Args: {e.args}")
            print(f"Full traceback:")
            traceback.print_exc()


# async def main():
#     trader = TraderOrchestrator()
#     multitoken = MultiTokenTrader(
#         trader.market_fetcher,
#         trader.indicator,
#         trader.agent_ensemble,
#         trader.risk,
#         trader.executor
#     )
#     await multitoken.evaluate_and_trade_top_tokens()
#     await trader.run_cycle()


# if __name__ == "__main__":
#     asyncio.run(main())