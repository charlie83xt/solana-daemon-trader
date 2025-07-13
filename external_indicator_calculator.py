import pandas as pd
import pandas_ta as ta
import httpx
# For making asynchronous HTTP requests to external agents
import asyncio

class IndicatorCalculator:
    def compute_indicators(self, price_list: list) -> dict:
        df = pd.DataFrame(price_list, columns=["close"])

        # Simple moving averages
        df["sma_20"] = ta.sma(df["close"], length=20)
        df["sma_50"] = ta.sma(df["close"], length=50)

        # RSI
        df["rsi"] = ta.rsi(df["close"], length=14)

        # MACD
        macd = ta.macd(df["close"])
        df = pd.concat([df, macd], axis=1)

        # Get latest values
        latest = df.iloc[-1]

        def safe_float(x, fallback=0.0):
            return float(x) if not pd.isna(x) else fallback

        return {
            'price': safe_float(latest["close"]),
            'sma_20': safe_float(latest["sma_20"]),
            'sma_50': safe_float(latest["sma_50"]),
            'rsi': safe_float(latest["rsi"]),
            'macd': safe_float(latest["MACD_12_26_9"]),
            'macd_signal': safe_float(latest["MACDs_12_26_9"]),
            'macd_hist': safe_float(latest["MACDh_12_26_9"]),
        }

