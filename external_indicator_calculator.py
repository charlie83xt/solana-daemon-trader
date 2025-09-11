import pandas as pd
# import pandas_ta as ta
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
import httpx
# For making asynchronous HTTP requests to external agents
import asyncio

class IndicatorCalculator:
    def compute_indicators(self, price_list: list) -> dict:
        if not price_list or len(price_list) < 50:
            # print(f"[IndicatorCalculator] not enough price data to compute indicators")
            return None

        df = pd.DataFrame(price_list, columns=["close"])

        # Simple moving averages
        # df["sma_20"] = ta.sma(df["close"], length=20)
        # df["sma_50"] = ta.sma(df["close"], length=50)

        df["sma_20"] = SMAIndicator(close=df["close"], window=20).sma_indicator()
        df["sma_50"] = SMAIndicator(close=df["close"], window=50).sma_indicator()       

        # RSI
        # df["rsi"] = ta.rsi(df["close"], length=14)
        df["rsi"] = RSIIndicator(close=df["close"], window=14).rsi()

        # MACD
        # macd = ta.macd(df["close"])
        # df = pd.concat([df, macd], axis=1)

        macd_instance = MACD(close=df["close"], window_slow=26, window_fast=12, window_sign=9)
        df["macd"] = macd_instance.macd()
        df["macd_signal"] = macd_instance.macd_signal()
        df["macd_hist"] = macd_instance.macd_diff()

        if df.empty or df.isna().all().all():
            # print(f"[IndicatorCalculator] Computed DataFrame is empty or NaN")
            return {}

        # Get latest values
        latest = df.iloc[-1]

        def safe_float(x, fallback=0.0):
            return float(x) if not pd.isna(x) else fallback

        return {
            'price': safe_float(latest["close"]),
            'sma_20': safe_float(latest["sma_20"]),
            'sma_50': safe_float(latest["sma_50"]),
            'rsi': safe_float(latest["rsi"]),
            'macd': safe_float(latest["macd"]), # before latest["MACD_12_26_9"]
            'macd_signal': safe_float(latest["macd_signal"]), # before latest["MACDs_12_26_9"]
            'macd_hist': safe_float(latest["macd_hist"]), # before latest["MACDh_12_26_9"]
        }

