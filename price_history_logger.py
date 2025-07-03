import os
import csv
from datetime import datetime 
from pycoingecko import CoinGeckoAPI
from log_router import LogRouter

class PriceHistoryLogger:
    def __init__(self, token_id="solana", vs_currency="usd", log_file="logs/sol_price_history.csv"):
        self.cg = CoinGeckoAPI()
        self.token_id = token_id
        self.vs_currency = vs_currency
        self.log_file = log_file
        self._ensure_file()
        self.logger = LogRouter()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "price", "volume"])


    def fetch_and_log(self):
        try:
            data = self.cg.get_coin_market_chart_by_id(id=self.token_id, vs_currency=self.vs_currency, days=1)
            latest_price = data['prices'][-1][1]
            latest_vol = data['total_volumes'][-1][1]
            now = datetime.utcnow().isoformat()

            with open(self.log_file, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([now, latest_price, latest_vol])

            print(f"[PriceLogger] {now} - Price: {latest_price}, Volume: {latest_vol}")
            self.logger.log_local_and_remote(self.log_file)
            return latest_price, latest_vol

        except Exception as e:
            print(f"[PriceLogger] Error fetching or writing price: {e}")
            return None