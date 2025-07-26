from agents.base_agent import BaseAgent
import os


class RuleBasedAgent(BaseAgent):
    def __init__(self):
        super().__init__("RuleBased")
        self.max_position = os.getenv("MAX_POSITION", 0.05)
        

    # async def get_decision(self, indicators):
    #     print("[RuleBasedAgent] Called with indicators", indicators)
    #     return {"action": "BUY", "amount": 0.05, "confidence": 0.8}

    async def get_decision(self, indicators):
        if not indicators or len(indicators) < 4:
            print(f"[{self.__class__.__name__}] Insufficient indicators. Returning HOLD.")
            return {"action": "HOLD", "amount": 0.0, "confidence": 0.0}
        
        price = indicators["price"]
        sma20 = indicators["sma_20"]
        sma50 = indicators["sma_50"]
        rsi = indicators["rsi"]
        macd = indicators["macd"]

        decision = {"action": "HOLD", "amount": 0.0, "confidence": 0.5}

        # BUY signal
        if rsi < 30 and macd > 0 and sma20 > sma50:
            decision["action"] = "BUY"
            decision["amount"] = float(self.max_position)
            decision["confidence"] = 0.85

        # SELL signal
        elif rsi > 70 and macd < 0 and sma20 < sma50:
            decision["action"] = "SELL"
            decision["amount"] = float(self.max_position)
            decision["confidence"] = 0.85

        return decision