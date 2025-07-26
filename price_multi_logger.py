import os
import csv
from datetime import datetime 
from pycoingecko import CoinGeckoAPI
# from log_router import LogRouter
# from log_paths import PRICE_LOG, get_log_path
from real_market_data import RealMarketDataFetcher
from db_logger import log_price_history


class PriceMultiLogger:
    def __init__(self, token_symbols: list[str], fetcher=None):
        self.token_symbols = token_symbols or ['SOL']
        self.fetcher = fetcher or RealMarketDataFetcher()
        # self.logger = LogRouter(use_drive=True)


    def fetch_and_log_all(self):
        for symbol in self.token_symbols:
            try:
                price = self.fetcher.fetch_current_price(symbol)
                volume = self.fetcher.fetch_current_volume(symbol)
                timestamp = datetime.utcnow().isoformat()

                log_price_history(
                    timestamp=timestamp,
                    symbol=symbol, 
                    price=price, 
                    volume=volume
                )
                # log_file = get_log_path(f"{symbol.lower()}_price_log.csv")

                # # Ensure file add header
                # if not os.path.exists(log_file):
                #     with open(log_file, "w", newline="") as f:
                #         writer = csv.writer(f)
                #         writer.writerow(["timestamp", "price", "volume"])

                # # Append price log
                # with open(log_file, "a", newline="") as f:
                #     writer = csv.writer(f)
                #     writer.writerow([timestamp, price, volume])

                print(f"[PriceLogger] {timestamp} - {symbol}: Price={price}, Volume={volume}")
                # self.logger.log_local_and_remote(log_file)

            except Exception as e:
                print(f"[PriceLogger] Error logging price for {symbol}: {e}")