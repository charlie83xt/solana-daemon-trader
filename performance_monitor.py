import csv
from collections import deque
from log_router import LogRouter


class PerformanceMonitor:
    def __init__(self, log_file="logs/trade_log.csv", window=10):
        self.log_file = log_file
        self.window = window # Number of recent trades to evaluate
        self.logger = LogRouter(use_drive=True)


    def evaluate(self):
        trades = deque(maxlen=self.window)

        try:
            csv_data = self.logger.download_log(self.log_file)
            if not csv_data:
                print(f"[PerformanceMonitor] No trade data available.")
                return None
            
            reader = csv.DictReader(csv_data.strip().splitlines())
            # with open(self.log_file, newline="") as f:
            #     reader = csv.DictReader(f)
                for row in reader:
                    if row.get("pnl"):
                        try:
                            trades.append({
                                "pnl": float(row["pnl"]),
                                "return_pct": float(row["return_pct"]),
                                "confidence": float(row["confidence"])
                            })
                        except ValueError:
                            continue
        except Exception as e:
            print(f"[PerformanceMonitor] Error reading log: {e}")
            return None

        if not trades:
            return None

        avg_pnl = sum(t["pnl"] for t in trades) / len(trades)
        avg_return = sum(t["return_pct"] for t in trades) / len(trades)
        win_rate = sum(1 for t in trades if t["pnl"] > 0) / len(trades)

        return {
            "avg_pnl": round(avg_pnl, 4),
            "avg_return": round(avg_return, 4),
            "win_rate": round(win_rate, 2)
        }