import asyncio
import os
from dotenv import load_dotenv
from jupiter_swapper import JupiterSwapper
from types import SimpleNamespace

async def main():
    load_dotenv()

    # Simulated executor with wallet
    class DummyExecutor:
        def __init__(self):
            import json
            from solders.keypair import Keypair as SoldersKeypair
            key_json = json.loads(os.getenv("PRIVATE_KEY_JSON"))
            self.keypair = SoldersKeypair.from_bytes(bytes(key_json))


    executor = DummyExecutor()
    swapper = JupiterSwapper(executor)

    # Test token (JUP on devnet)
    test_token = {
    "symbol": "USDC",
    "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    }   

    # Fake decision
    test_decision = {
        "action": "BUY",
        "amount": 0.001,
        "confidence": 0.95
    }

    await swapper.execute_swap(test_token, test_decision)

if __name__ == '__main__':
    asyncio.run(main())