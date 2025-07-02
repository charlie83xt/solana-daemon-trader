import asyncio
import os
from dotenv import load_dotenv
from orchestrator import TraderOrchestrator

async def main():
    load_dotenv()
    interval = int(os.getenv("POLL_INTERVAL", 300)) # run every 5 mins

    print(f"[Runner] Starting trader loop on Devnet every {interval} seconds...")

    orchestrator = TraderOrchestrator()

    while True:
        try:
            await orchestrator.run_cycle()
        except Exception as e:
            print(f"[Runner] Error during run_cycle: {e}")
        await asyncio.sleep(interval)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
            print("\n[Runner] Exiting.")