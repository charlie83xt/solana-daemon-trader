import os
import asyncio
from dotenv import load_dotenv
# from solana_data_extractor_adjusted import SolanaDataExtractor
from external_indicator_calculator import IndicatorCalculator
from external_ai_agent_decision import AIAgentCaller
from risk_manager import RiskManager
from executor import TransactionExecutor
from real_market_data import RealMarketDataFetcher
from agents.openai_agent import OpenAIAgent
from agents.threshold_agent import ThresholdAgent
from agents.agent_orchestrator import AgentOrchestrator


class TraderOrchestrator:
    def __init__(self):
        load_dotenv(override=True)

        self.rpc_url = os.getenv("SOLANA_RPC_URL")
        self.max_position = float(os.getenv("MAX_POSITION_SIZE", 0.1))
        self.max_daily_loss = float(os.getenv("MAX_DAILY_LOSS", 1.0))
        self.market_fetcher = RealMarketDataFetcher()
        
        # self.extractor = SolanaDataExtractor(self.rpc_url)
        self.indicator = IndicatorCalculator()
        self.ai_agent = AIAgentCaller()
        self.executor = TransactionExecutor(self.rpc_url)
        self.risk = RiskManager(
            max_daily_loss = self.max_daily_loss,
            cooldown_minutes = int(os.getenv("COOLDOWN_MINUTES", 10))
        )
        self.agent_ensemble = AgentOrchestrator([
            OpenAIAgent(),
            ThresholdAgent()
            # More agents can be added here later
        ])

    async def run_cycle(self):
        try:
            # 1) Get price history
            # raw_data = self.market_fetcher.cg.get_coin_market_chart_by_id(id='solana', vs_currency='usd', days='2')
            # price_list = [point[1] for point in raw_data['prices']]
            price_list = self.market_fetcher.fetch_price_history()

            # 2) Compute indicators
            indicators = self.indicator.compute_indicators(price_list)
            if not indicators:
                print("[Orchestrator] Marklet data unavailable. Skipping cycle.")
                return

            # 3) Get AI decision
            decision = await self.agent_ensemble.resolve_decision(indicators)
            print(f"[Final Decision] {decision['action']} {decision['amount']} SOL @ confidence {decision['confidence'] * 100:.1f}%")

            if not self.risk.approve_trade(decision, indicators):
                print("[Orchestrator] RiskManager blocked this trade.")
                return

            # 4) Act on decision
            action = decision.get('action', 'HOLD')
            amount = float(decision.get('amount', 0))

            if action == 'BUY':
                amount = min(self.max_position, decision['amount'])
                print(f"[Orchestrator] Decided to BUY {amount} SOL")
                self.executor.execute_trade('BUY', amount)

            elif action == 'SELL':
                amount = min(self.max_position, decision['amount'])
                print(f"[Orchestrator] Decided to SELL {amount} SOL")
                self.executor.execute_trade('SELL', amount)

            else:
                print("[Orchestrator] No action taken this cycle.")

            self.risk.log_trade(action, amount, indicators["price"], decision.get("confidence", 1.0))

        except Exception as e:
            print(f"[Orchestrator] Error during run_cycle: {e}")


if __name__ == "__main__":
    trader = TraderOrchestrator()
    asyncio.run(trader.run_cycle())