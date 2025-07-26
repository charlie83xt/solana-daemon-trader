from pycoingecko import CoinGeckoAPI
from cg_symbol_map import COINGECKO_IDS
import sqlite3
from db import get_connection


class RealMarketDataFetcher:
    def __init__(self):
        self.cg = CoinGeckoAPI()

    def fetch_price_history(self, symbol, lookback=50) -> list:
        # conn = sqlite3.connect("trading.db")
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT price FROM price_history
            WHERE symbol = %s
            ORDER BY timestamp DESC
            LIMIT %s 
        """, (symbol.upper(), lookback))
        # try:
            # cg_id = COINGECKO_IDS.get(symbol.upper(), symbol.lower())
            # data = self.cg.get_coin_market_chart_by_id(id='solana', vs_currency='usd', days=days)
        prices = [point[0] for point in c.fetchall()]
        conn.close()
        return prices[::-1]
        # except Exception as e:
        #     print(f"[DataFetcher] Error fetching data: {e}")
        #     return []
    
    def fetch_sol_usdc_indicators(self):
        try:
            data = self.cg.get_coin_market_chart_by_id(id='solana', vs_currency='usd', days='2')
            prices = [point[1] for point in data['prices']]
            volumes = [point[1] for point in data['total_volumes']]

            # Simple indicators
            current_price = prices[-1]
            sma_20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else current_price
            sma_50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else current_price
            rsi = self.simple_rsi(prices[-15:]) # Simplistic RSI

            return {
                "price": current_price,
                "sma_20": round(sma_20, 2),
                "sma_50": round(sma_50, 2),
                "rsi": round(rsi, 2),
                "volume_24h": round(sum(volumes), 2)
            }

        except Exception as e:
            print(f"[DataFetcher] Error fetching data: {e}")
            return {}

    
    def simple_rsi(self, price_series):
        gains = [max(price_series[i+1] - price_series[i], 0) for i in range(len(price_series) - 1)]
        losses = [max(price_series[i] - price_series[i+1], 0) for i in range(len(price_series) - 1)]

        avg_gain = sum(gains) / len(gains)
        avg_loss = sum(losses) / len(losses) if sum(losses) != 0 else 1e-6

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi


    def fetch_current_price(self, symbol: str) -> float:

        try:
            cg_id = COINGECKO_IDS.get(symbol.upper())
            if not cg_id:
                print(f"[DataFetcher] Unknown coingecko ID for symbol {symbol}")
                return 0.0
            data = self.cg.get_price(ids=cg_id, vs_currencies='usd')
            return float(data[cg_id]['usd'])
        except Exception as e:
            print(f"[DataFetcher] Error fetching current price for {symbol}: {e}")
            return 0.0

    def fetch_current_volume(self, symbol: str) -> float:
        try:
            cg_id = COINGECKO_IDS.get(symbol.upper())
            if not cg_id:
                print(f"[DataFetcher] Unknown coingecko ID for symbol {symbol}")
                return 0.0
            data = self.cg.get_coin_market_chart_by_id(id=cg_id, vs_currency='usd', days=1)
            return float(data['total_volumes'][-1][1])
        except Exception as e:
            print(f"[DataFetcher] Error fetching volume for {symbol}: {e}")
            return 0.0
