import os
# import csv
from datetime import datetime 
from pycoingecko import CoinGeckoAPI
from cg_symbol_map import COINGECKO_IDS
# from log_paths import PRICE_LOG
from db_logger import log_price_history
# 
class PriceHistoryLogger:
    def __init__(self, db_path="trading.db"):
        self.cg = CoinGeckoAPI()
        self.symbol_to_id = COINGECKO_IDS
        self.db_path = db_path


    # def log_price_history(self, symbol: str, price: float, volume: float):
    #     try:
    #         now = datetime.utcnow().isoformat()
    #         with sqlite3.connect(self.db_path) as conn:
    #             c = conn.cursor()
    #             c.execute("""
    #                 INSERT INTO price_history (timestamp, symbol, price, volume)
    #                 VALUES (?, ?, ?, ?)
    #             """, 
    #             (now, symbol, price, volume))
    #         conn.commit()
    #     except Exception as e:
    #         print(f"[PriceLogger] Error logging price for {symbol}: {e}")

    def fetch_and_log(self):
        try:
            data = self.cg.get_coin_market_chart_by_id(id=self.token_id, vs_currency=self.vs_currency, days=1)
            latest_price = data['prices'][-1][1]
            latest_vol = data['total_volumes'][-1][1]
            now = datetime.utcnow().isoformat()

            log_price_history(
                now,
                self.token_id.upper(),
                latest_price,
                latest_vol
            )

            # print(f"[PriceLogger] {now} - Price: {latest_price}, Volume: {latest_vol}")
            # self.logger.log_local_and_remote(self.log_file)
            return latest_price, latest_vol

        except Exception as e:
            print(f"[PriceLogger] Error fetching or writing price: {e}")
            return None