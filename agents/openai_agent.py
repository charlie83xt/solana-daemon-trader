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
        prompt = f"""
        You are a Solana crypto trading agent.

        Respond ONLY with a JSON object in the following format and nothing else: 
        {{"action": "BUY", "amount": 0.1, "confidence": 0.92}}

        Do not explain your answer. Do not include any text or formatting.

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