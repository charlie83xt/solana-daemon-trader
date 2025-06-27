import os
import openai
from openai import AsyncOpenAI
import json
import pandas as pd
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

class AIAgentCaller:
    def __init__(self):
        self.agent_type = os.getenv("AI_AGENT_TYPE", "openai").lower()
        self.openai_api_key = os.getenv("AI_AGENT_API_KEY")
        self.external_api_url = os.getenv("EXTERNAL_TRADING_SIGNAL_API_URL")
        openai.api_key = self.openai_api_key

    
    async def get_trade_decision(self, indicators):
        if self.agent_type == 'openai':
            return await self._call_openai(indicators)
        elif self.agent_type == "http_api":
            return await self._call_http_agent(indicators)
        else:
            print(f"[AI Agent] Unknown agent type: {self.agent_type}")
            return {"action": "HOLD", "confidence": 0.0, "amount": 0.0}

    async def _call_openai(self, indicators):
        prompt = f'''
        You are a Solana crypto trading AI. Your goal is to decide whether to BUY, SELL, or HOLD based on the market indicators below.

        Current Price: {indicators.get("price")}
        SMA_20: {indicators.get("sma_20")}
        SMA_50: {indicators.get("sma_50")}
        RSI: {indicators.get("rsi")}

        Respond in this exact JSON format:
        {{"action": "BUY", "amount": 0.1}}
        '''

        try:
            client = AsyncOpenAI(api_key=self.openai_api_key)

            response = await client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an expert crypto trading AI."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            content = response.choices[0].message.content
            decision = json.loads(content)
            decision.setdefault("confidence", 1.0)
            decision.setdefault("target_price", None)
            decision.setdefault("stop_loss", None)
            return decision
        except Exception as e:
            print(f"[AI Agent] OpenAI error: {e}")
            return {"action": "HOLD", "confidence": 0.0, "amount": 0.0}

    
    async def _call_http_agent(self, market_data):
        headers = {
            "Authorization": f"Bearer {self.external_api_key}",
            "Content-Type": "application/json"
        }
        try:
            async with httpx.AsyncClient() as client:
                print("[AI Agent] Sending market data to external API agent...")
                response = await client.post(
                    self.external_api_url,
                    json=market_data,
                    headers=headers,
                    timeout=20.0
                )
                response.raise_for_status()
                signal_response = response.json()

                if "signal" in signal_response:
                    return {
                        "action": signal_response.get("signal", "HOLD"),
                        "confidence": signal_response.get("confidence", 0.0),
                        "amount": signal_response.get("amount", 0.0),
                        "target_price": signal_response.get("target_price"),
                        "stop_loss": signal_response.get("stop_loss")
                    }
                else:
                    print("[AI Agent] Invalid response format.")
                    return {"action": "HOLD", "confidence": 0.0, "amount": 0.0}
        except httpx.RequestError as exc:
            print(f"[AI Agent] Request error: {exc}")
            return {"action": "HOLD", "confidence": 0.0, "amount": 0.0}
        except httpx.HTTPStatusError as exc:
            print(f"[AI Agent] Request error: {exc.respose.status_code} - {exc.respose.text}")
            return {"action": "HOLD", "confidence": 0.0, "amount": 0.0}







# Configuration
# c = "https://api.example.com/trading_signals/gnerate" # Placeholder for external trading signal AI agent API
# EXTERNAL_TRADING_SIGNAL_API_KEY = "YOUR_TRADING_SIGNAL_API_KEY" # Securely load api key

# async def get_trading_signal_from_external_agent(market_data: dict) -> dict:
#     """
#         Sends market data to an external AI agent and returns a trading signal
#     """
#     headers = {"Auhorization":f"Bearer {EXTERNAL_TRADING_SIGNAL_API_KEY}", "Content-Type":"application/json"}
#     async with httpx.AsyncClient() as client:
#         try:
#             print(f"Sending market data to external trading signal AI agent...")
#             response = await client.post(EXTERNAL_TRADING_SIGNAL_API_URL, json=market_data, headers=headers, timeout=20.0)
#             response.raise_for_status()
#             # Raise an exception for 4xx or 5xx status codes
#             return response.json()
#         except httpx.RequestError as exc:
#             print(f"An error occurred while requesting {exc.request.url!r}: {exc}")
#             return {"error": str(exc)}
#         except httpx.HTTPStatusError as exc:
#             print(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc.response.text}")
#             return {"error": exc.response.text}

# async def make_decision_based_on_external_signal(current_market_data: dict): 
#     """
#         Receives market data, gets a signal from an external agent, and makes a decision.
#     """
#     # In a real scenario, current_market_data would include processed OHLCV, indicators, etc.
#     # This example uses a simplified structure.

#     # Step 1: Send data to external AI agent for a signal
#     signal_response = await get_trading_signal_from_external_agent(current_market_data)
#     if signal_response and "error" not in signal_response:
#         signal = signal_response.get("signal")
#         confidence = signal_response.get("confidence", 0.0)
#         target_price = signal_response.get("target_price")
#         stop_loss = signal_response.get("stop_loss")

#         print(f"\nReceived Signal: {signal}, Confidence: {confidence*100:.2f}%")
#         if target_price: print(f"Target Price: {target_price}")
#         if stop_loss: print(f"Stop Loss: {stop_loss}")

#         # Step 2: Internal DApp logic to interpret and act on the signal
#         # This is where your internal Risk Management Agent would come into play.
#         if signal == "BUY" and confidence > 0.75: # Example threshold
#             print("Internal DApp Decision: Oroceeding with BUY order to high confidence signal.")
#             # Here we will pass this to our Risk Management Agent for approval 
#             # and then to the Order Execution System
#             return {"action": "BUY", "confidence": confidence, "target_price": target_price, "stop_loss": stop_loss}
#         elif signal == "SELL" and confidence > 0.75:
#             print("Internal Dapp Decision: Proceeding with SELL order due to high confidence signal.")
#             # Pass to Risk Management Agen and Order Execution System
#             return {"action": "SELL", "confidence": confidence, "target_price": target_price, "stop_loss": stop_loss}
#         else: 
#             print("Internal Dapp Decision: HOLD (Signal not strong enough or not actionable).")
#             return {"action": "HOLD"}
#     else:
#         print("Internal Dapp Decision: HOLD (Failed o get valid signal from external agent).")
#         return {"action": "HOLD", "error": signal_response.get("error", "Unknown error")}

# if __name__ == "__main__":
#     # Example of market data that would be sent to the external AI agent
#     sample_market_data = {
#         "symbol": "SOL/USDC",
#         "current_price": 150.25,
#         "volume_24h": 1234567.89,
#         "rsi_14": 45.67,
#         "macd_histogram": 0.52,
#         "on_chain_sentiment_score": 0.78,
#         "news_sentiment": "positive"
#     }
#     try:
#         decision_result = asyncio.run(make_decision_based_on_external_signal(sample_market_data))
#         print(f"\nFinal DApp Action: {decision_result}")

#         # Simulate a scenario where the external agent might give strong SELL signal
#         print("\nSimulating a strong SELL scenario:")
#         sell_market_data = {
#             "symbol": "SOL/USDC",
#             "current_price": 160.00,
#             "volume_24h": 2000000.00,
#             "rsi_14": 80.12, # Overbought
#             "macd_histogram": -1.20, # Bearish divergence
#             "on_chain_sentiment_score": 0.20,
#             "news_sentiment": "negative"
#         }

#         # Mocking the external agent's response for demonstration
#         # In a real system, this would be a call to the actual API

#         async def mock_sell_signal_agent(data):
#             reurn {"signal": "SELL", "confidence": 0.90, "target_price": 140.00, "stop_loss": 165.00}

#             # Temporarily replace the actual API call with the mock for this scenario
#             original_get_signal = get_trading_signal_from_external_agent
#             get_trading_signal_from_external_agent = mock_sell_signal_agent

#             dcision_result_sell = asyncio.run(make_decision_based_on_external_signal(sell_market_data))
#             print(f"\nFinal DApp Action for SELL scenario: {decision_result_sell}")

#             # Restore original function
#             get_trading_signal_from_external_agent = original_get_signal
    
#     except KeyboardInterrupt:
#         print("\nExiting")



