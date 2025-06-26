import os
import asyncio
from dotenv import load_dotenv
from solana_data_extractor_adjusted import SolanaDataExtractor
from external_indicator_calculator import IndicatorCalculator
from external_ai_agent_decision import AIAgentCaller
from executor import TransactionExecutor

class TraderOrchestrator:
    def __init__(self):
        load_dotenv()

        self.rpc_url = os.getenv("SOLANA_RPC_URL")
        self.max_position = float(os.getenv("MAX_POSITION_SIZE", 0.1))
        self.max_daily_loss = float(os.getenv("MAX_POSITION_SIZE", 0.1))
        
        self.extractor = SolanaDataExtractor(self.rpc_url)
        self.indicator = IndicatorCalculator()
        self.ai_agent = AIAgentCaller()
        self.executor = TransactionExecutor(self.rpc_url)

    async def run_cycle(self):
        # 1) Get market data
        market_data = await self.extractor.get_market_data()

        # 2) Compute indicators
        indicators = self.indicator.compute_indicators(market_data)

        # 3) Get AI decision
        decision = self.ai_agent.get_trade_decision(indicators)

        # 4) Check Risk (basic example)
        if decision['action'] == 'BUY':
            amount = min(self.max_position, decision['amount'])
            print(f"[Orchestrator] Decided to BUY {amount} SOL")
            self.executor.execute_trade('BUY', amount)

        elif decision['action'] == 'SELL':
            amount = min(self.max_position, decision['amount'])
            print(f"[Orchestrator] Decided to SELL {amount} SOL")
            self.executor.execute_trade('SELL', amount)

        else:
            print("[Orchestrator] No action taken this cycle.")
