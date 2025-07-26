# token_performance.py
import csv
from datetime import datetime, timedelta
from collections import defaultdict
# from log_router import LogRouter
from token_scanner import fetch_top_tokens
import sqlite3
from db import get_connection

BOOTSTRAP_SYMBOLS = ["SOL", "USDT", "PYUSD", "WIF", "POPCAT", "BONK", "JUP"]

class TokenPerformanceTracker:
    def __init__(self, db_path="trading.db", lookback_days=3):
        self.db_path = db_path
        self.lookback_days = lookback_days
        # self.logger = LogRouter(use_drive=True)
        self.bootstrap_symbols = BOOTSTRAP_SYMBOLS

    def top_tokens_by_pnl(self, limit=5):
        try:
            # conn = sqlite3.connect(self.db_path)
            conn = get_connection()
            c = conn.cursor()

            c.execute("""
                SELECT symbol, SUM(pnl) AS total_pnl
                FROM trades 
                WHERE pnl is NOT NULL
                GROUP BY symbol
                ORDER BY total_pnl DESC
                LIMIT %s
            """, [limit])
            rows = c.fetchall()
            conn.close()
            if not rows:
                return self.bootstrap_symbols
        except Exception as e:
            print(f"[TokenPerformanceTracker] Error fetching top tokens: {e}")
            return self.bootstrap_symbols
        # now = datetime.now().utcnow()
        # cutoff = now - timedelta(days=self.lookback_days)
        # pnl_by_token = defaultdict(list)

        # try:
        #     content = self.logger.download_log(self.log_path)
        #     if not content:
        #         print("[TokenTracker] No trade_log found or empty.")
        #         fallback = [t['symbol'] for t in fetch_top_tokens(limit=3)]
        #         return fallback

        #     reader = csv.DictReader(content.strip().splitlines())
        #     for row in reader:  
        #         try:
        #             timestamp = datetime.fromisoformat(row["timestamp"])
        #             if timestamp < cutoff:
        #                 continue

        #             symbol = row.get("symbol", "UNKNOWN")
        #             pnl = float(row.get("pnl", 0.0))
        #             pnl_by_token[symbol].append(pnl)
        #         except Exception:
        #             continue
        # except Exception as e:
        #     print(f"[TokenTracker] Error reading log: {e}")
        #     return []

        # avg_pnl = {sym: sum(pnls)/len(pnls) for sym, pnls in pnl_by_token.items() if pnls}
        # top = sorted(avg_pnl.items(), key=lambda x: x[1], reverse=True)[:top_n]
        # return [sym for sym, _ in top]