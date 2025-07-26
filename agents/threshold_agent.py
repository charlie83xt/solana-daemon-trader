# agents/threshold_agent.py

from agents.base_agent import BaseAgent

class ThresholdAgent(BaseAgent):
    def __init__(self):
        super().__init__("ThresholdAgent")

    
    async def get_decision(self, indicators):
        if not indicators or len(indicators) < 4:
            print(f"[{self.__class__.__name__}] Insufficient indicators. Returning HOLD.")
            return {"action": "HOLD", "amount": 0.0, "confidence": 0.0}
        rsi = indicators.get("rsi", 50)
        macd = indicators.get("macd", 0)
        macd_signal = indicators.get("macd_signal", 0)

        action = "HOLD"
        confidence = 0.7
        amount = 0.05 # be conservative by default

        if rsi < 30 and macd > macd_signal:
            action = "BUY"
            confidence = 0.9
        elif rsi > 70 and macd < macd_signal:
            action = "SELL"
            confidence = 0.9

        return {
            "action": action,
            "amount": amount,
            "confidence": confidence
        }