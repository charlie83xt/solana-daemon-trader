import csv
from collections import deque
# from log_router import LogRouter
import sqlite3
from db import get_connection


class PerformanceMonitor:
    def __init__(self, db_path="trading.db", window=10):
        self.db_path = db_path
        self.window = window # Number of recent trades to evaluate
        # self.logger = LogRouter(use_drive=True)


    def evaluate(self):
        trades = deque(maxlen=self.window)

        try:
            # with sqlite3.connect(self.db_path) as conn:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT pnl, return_pct, confidence
                    FROM trades
                    WHERE pnl IS NOT NULL
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, [self.window])
                rows = cursor.fetchall()

            for pnl, ret, conf in rows:
                try:
                    trades.append({
                        "pnl": float(pnl),
                        "return_pct": float(ret),
                        "confidence": float(conf)
                    })
                except (TypeError, ValueError):
                    continue

            if not trades:
                # print(f"[PerformanceMonitor] Not recent trades found.")
                return None

            avg_pnl = sum(float(t["pnl"]) for t in trades) / len(trades)
            avg_return = sum(float(t["return_pct"]) for t in trades) / len(trades)
            win_rate = sum(1 for t in trades if float(t["pnl"]) > 0) / len(trades)

            return {
                "avg_pnl": round(avg_pnl, 4),
                "avg_return": round(avg_return, 4),
                "win_rate": round(win_rate, 2)
            }
        except Exception as e:
            print(f"[PerformanceMonitor] Error evaluating DB trades: {e}")
            return None