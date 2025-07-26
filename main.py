import asyncio
import os
from dotenv import load_dotenv
from orchestrator import TraderOrchestrator
from price_history_logger import PriceHistoryLogger
from multi_token_trader import MultiTokenTrader
from price_multi_logger import PriceMultiLogger
from token_performance import TokenPerformanceTracker
from db import initialize_tables
# from external_indicator_calculator import IndicatorCalculator
import traceback

# Inject Google Drive credentials from environment into local files
# secrets_json = os.getenv("GOOGLE_CLIENT_SECRETS_JSON", "")
# mycreds_txt = os.getenv("GOOGLE_MYCREDS_TXT", "")

# if secrets_json.strip().startswith("{"):
#     with open("client_secrets.json", "w") as f:
#         f.write(secrets_json)

# if mycreds_txt.strip().startswith("{"):
#     with open("mycreds.txt", "w") as f:
#         f.write(mycreds_txt)

async def main():
    initialize_tables()
    load_dotenv()
    interval = int(os.getenv("POLL_INTERVAL", 300)) # run every 5 mins

    print(f"[Runner] Starting trader loop every {interval} seconds...")

    # market_fetcher = RealMarketDataFetcher()
    orchestrator = TraderOrchestrator()

    performance_tracker = TokenPerformanceTracker(db_path="trading.db")
    top_symbols = performance_tracker.top_tokens_by_pnl()
    if not top_symbols:
        print(f"[Main] Nop tokens found. Using default fallback ['SOL']")
        top_symbols = ['SOL']

    price_logger = PriceMultiLogger(top_symbols)

    multitoken = MultiTokenTrader(
        market_fetcher=orchestrator.market_fetcher,
        indicator=orchestrator.indicator,
        agent_ensemble=orchestrator.agent_ensemble,
        risk=orchestrator.risk,
        keypair=orchestrator.keypair
    )
    
    await orchestrator.run_cycle()

    while True:
        try:
            print("\n--- [Cycle Start] ---")
            price_logger.fetch_and_log_all()

            trade_executed = await multitoken.evaluate_and_trade_top_tokens()

            enable_fallback = os.getenv("ENABLE_ORCHESTRATOR_FALLBACK", "True").lower() == "true"
            if not trade_executed and enable_fallback:
                await orchestrator.run_cycle()

            print("--- [Cycle Complete] ---\n")
        except Exception as e:
            print(f"[Runner] Error during run_cycle: {e}")
            print(f"[Runner] Error during run_cycle().")
            print(f"Type: {type(e)}")
            print(f"Args: {e.args}")
            print(f"Full traceback:")
            traceback.print_exc()
        await asyncio.sleep(interval)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
            print("\n[Runner] Exiting.")