# agents/openai_agent.py
from openai import AsyncOpenAI
import os
import json
from agents.base_agent import BaseAgent

class OpenAIAgent(BaseAgent):
    def __init__(self):
        super().__init__("OpenAI")
        self.api_key = os.getenv("AI_AGENT_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key)

    
    async def get_decision(self, indicators):
        if not indicators or len(indicators) < 4:
            print(f"[{self.__class__.__name__}] Insufficient indicators. Returning HOLD.")
            return {"action": "HOLD", "amount": 0.0, "confidence": 0.0}
            
        prompt = f"""
        You are a Solana crypto trading agent.

        You must output ONLY a JSON object like: 
        {{"action": "BUY", "amount": 0.05, "confidence": 0.92}}

        Use this logic:
        - BUY if price is rising, MACD is positive, RSI is below 70, and SMA20 > SMA50
        - SELL if RSI > 70, MACD is negative, or price is dropping, and SMA20 < SMA50
        - HOLD in all other cases

        Use confidence between 0.5 (low) and 1.0 (high), based on how strong the indicators are.

        Only output the JSON. Do not explain your answer. Do not include any text or formatting.

        Indicators:
        Price: {indicators["price"]}
        SMA20: {indicators["sma_20"]}
        SMA20: {indicators["sma_50"]}
        RSI: {indicators["rsi"]}
        MACD: {indicators["macd"]}

        """

        try:
            res = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a crypto tradiong agent."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            if not res.choices or not res.choices[0].message.content:
                raise ValueError("OpenAI response missing or empty")
            print(f"[OpenAIAGent] Raw model reply: {res.choices[0].message.content!r}")
            content = res.choices[0].message.content.strip()
            return json.loads(content)
        except Exception as e:
            print(f"[OpenAIAgent] Error: {e}")
            return {"action": "HOLD", "amount": 0.0, "confidence": 0.0}