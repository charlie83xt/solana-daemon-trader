import asyncio
import os
from agents.rule_based_agent import RuleBasedAgent


# Simulated version of your RuleBasedAgent and BaseAgent
# class BaseAgent:
#     def __init__(self, name):
#         self.name = name


# class RuleBasedAgent(BaseAgent):
#     def __init__(self):
#         super().__init__("RuleBased")


    # async def get_decision(self, indicators):
    #     print("[RuleBasedAgent] Called with indicators:", indicators)
    #     # Example basic decision rule (you can customize logic here)
    #     if indicators.get("rsi", 50) < 30:
    #         return {"action": "BUY", "amount": 0.05, "confidence": 0.8}
    #     elif indicators.get("rsi", 50) > 70:
    #         return {"action": "SELL", "amount": 0.05, "confidence": 0.8}
    #     else:
    #         return {"action": "HOLD", "amount": 0.0, "confidence": 0.6}


# Sample mock indicators (adjust as needed)
mock_indicators = {
    "price": 170.0,
    "sma_20": 165.0,
    "sma_50": 160.0,
    "rsi": 72,  # Test a SELL signal
    "macd": 1.2,
    "macd_signal": 1.1,
    "macd_hist": 0.1,
    "symbol": "SOL"
}


async def test_agent():
    agent = RuleBasedAgent()
    decision = await agent.get_decision(mock_indicators)
    print("[Test] Final decision:", decision)


if __name__ == "__main__":
    asyncio.run(test_agent())

