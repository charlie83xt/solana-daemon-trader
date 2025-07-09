print(">>> Starting main.py")
try:
    import asyncio
    import os
    from dotenv import load_dotenv
    from orchestrator import TraderOrchestrator
    from price_history_logger import PriceHistoryLogger
    from multi_token_trader import MultiTokenTrader
    from price_multi_logger import PriceMultiLogger
    from token_performance import TokenPerformanceTracker
    # from external_indicator_calculator import IndicatorCalculator
    import traceback
    print(" Imports sucessful")
except Exception as e:
    print(">>> Import failed", e)
print(">>> Environment loaded")

async def main():
    load_dotenv()
    interval = int(os.getenv("POLL_INTERVAL", 300)) # run every 5 mins

    print(f"[Runner] Starting trader loop every {interval} seconds...")

    # market_fetcher = RealMarketDataFetcher()
    orchestrator = TraderOrchestrator()
    multitoken = MultiTokenTrader(
        orchestrator.market_fetcher,
        orchestrator.indicator,
        orchestrator.agent_ensemble,
        orchestrator.risk,
        orchestrator.keypair
    )

    performance_tracker = TokenPerformanceTracker()
    top_symbols = performance_tracker.top_tokens_by_pnl()
    price_logger = PriceMultiLogger(top_symbols)

    
    await orchestrator.run_cycle()

    while True:
        try:
            print("\n--- [Cycle Start] ---")
            price_logger.fetch_and_log_all()
            trade_executed = await multitoken.evaluate_and_trade_top_tokens()
            if not trade_executed:
                await orchestrator.run_cycle()
            print("--- [Cycle Complete] ---\n")
        except Exception as e:
            print(f"[Runner] Error during run_cycle: {e}")
            # print(f"[Runner] Error during run_cycle().")
            # print(f"Type: {type(e)}")
            # print(f"Args: {e.args}")
            # print(f"Full traceback:")
            # traceback.print_exc()
        await asyncio.sleep(interval)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
            print("\n[Runner] Exiting.")