# backfill_price_data.py
from pycoingecko import CoinGeckoAPI
import sqlite3
from datetime import datetime
from cg_symbol_map import COINGECKO_IDS
from db import get_connection


cg = CoinGeckoAPI()
DB_PATH = "trading.db"


## Here we probably need somthing like insert if coin on COINGECKO_IDS
symbol_to_id = COINGECKO_IDS
# symbol_to_id = {
#     "JUP": "jupiter-exchange-solana"
# }


def backfill_prices(symbol: str, days: int = 3):
    token_id = symbol_to_id.get(symbol.upper())
    if not token_id:
        print(f"[Backfill] Unknown token ID for {symbol}")
        return


    try:
        data = cg.get_coin_market_chart_by_id(id=token_id, vs_currency="usd", days=days)
        prices = data["prices"]
        volumes = data["total_volumes"]

        conn = get_connection()
        cursor = conn.cursor()

        # Start a transaction for efficiency
        conn.run("BEGIN")
        for price_point, vol_point in zip(prices, volumes):
            timestamp = datetime.utcfromtimestamp(price_point[0] / 1000).isoformat()
            price = price_point[1]
            vol = vol_point[1]

            # with sqlite3.connect(DB_PATH) as conn:
            # conn = get_connection()
            # cursor = conn.cursor()
            cursor.execute(
                        """
                        INSERT INTO price_history (timestamp, symbol, price, volume)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (timestamp, symbol.upper(), price, vol)
            )

        conn.commit()
        print(f"[Backfill] Inserted {len(prices)} rows for {symbol}")
    except Exception as e:
        print(f"[Backfill] Error for {symbol}: {e}")



if __name__ == "__main__":
    for sym in symbol_to_id:
        backfill_prices(sym, days=3)





