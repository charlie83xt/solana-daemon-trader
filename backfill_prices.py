from db_logger import log_price_history
from pycoingecko import CoinGeckoAPI
from datetime import datetime
import time


cg = CoinGeckoAPI()

def backfill_prices(symbol="SOL", cg_id="solana", vs_currency="usd", days=3):
    data = cg.get_coin_market_chart_by_id(id=cg_id, vs_currency=vs_currency, days=days)
    for price_point, vol_point in zip(data["prices"], data["total_volumes"]):
        ts = datetime.utcfromtimestamp(price_point[0] / 1000).isoformat()
        price = price_point[1]
        vol = vol_point[1]
        log_price_history(timestamp=ts, symbol=symbol, price=price, volume=vol)
    print(f" Backfilled {symbol} with {len(data['prices'])} entries")

backfill_prices()