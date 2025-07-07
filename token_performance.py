# token_performance.py
import csv
from datetime import datetime, timedelta
from collections import defaultdict


class TokenPerformanceTracker:
    def __init__(self, log_path="logs/trade_log.csv", lookback_days=3):
        self.log_path = log_path
        self.lookback_days = lookback_days


    def top_tokens_by_pnl(self, top_n=3):
        now = datetime.now().utcnow()
        cutoff = now - timedelta(days=self.lookback_days)
        pnl_by_token = defaultdict(list)

        try:
            with open(self.log_path, newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    timestamp = datetime.fromisoformat(row["timestamp"])
                    if timestamp < cutoff:
                        continue

                    symbol = row["symbol"]

                    try:
                        pnl = float(row.get("pnl", 0.0))
                        pnl_by_token[symbol].append(pnl)
                    except:
                        continue
        except FileNotFoundError:
            print("[TokenTracker] No trade_log.csv found.")
            return []

        avg_pnl = {sym: sum(pnls)/len(pnls) for sym, pnls in pnl_by_token.items() if pnls}
        top = sorted(avg_pnl.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [sym for sym, _ in top]