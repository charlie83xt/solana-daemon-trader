import pandas as pd
import asyncio
from external_indicator_calculator import IndicatorCalculator
from agents.agent_orchestrator import AgentOrchestrator
from datetime import datetime

class Backtester:
    def __init__(self, price_csv_path):
        self.df = pd.read_csv(price_csv_path)
        self.indicator_calc = IndicatorCalculator()
        self.agent_ensemble = AgentOrchestrator()
        self.trade_log = []


    def compute_all_indicators(self):
        prices = self.df["close"].tolist()
        indicators = self.indicator_calc.compute_indicators(prices)
        self.df = self.df.tail(len(prices))
        for key in indicators:
            self.df[key] = indicators[key]


    async def simulate_trades(self):
        for i in range(50, len(self.df)):
            row = self.df.iloc[i]
            indicators = {
                "price": row["close"],
                "rsi": row.get("rsi", 0),
                "macd": row.get("MACD_12_26_9", 0),
                "macd_hist": row.get("MACDh_12_26_9", 0),
                "sma_20": row.get("sma_20", 0),
                "sma_50": row.get("sma_50", 0),
                "symbol": "SOL"
            }

            decision = await self.agent_ensemble.resolve_decision(indicators)

            if decision["action"] == "HOLD":
                self.trade_log.append({
                    "timestamp": self.df.iloc[i]["timestamp"],
                    "price": row["close"],
                    "action": decision["action"],
                    "confidence": decision["confidence"]
                })

    def summary(self):
        if not self.trade_log:
            print("No trades were made.")
        return

        df = pd.DataFrame(self.trade_log)
        print("\n📊 Trades Summary:")
        print(df)
        df.to_csv("logs/backtest_trades.csv", index=False)


async def run_backtest():
    tester = Backtest("data/sol_usd_hourly.csv")
    tester.compute_all_indicators()
    await tester.simulate_trades()
    tester.summary()

if __name__ == "__main__":
    asyncio.run(run_backtest())