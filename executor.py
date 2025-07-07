import os
import json
from dotenv import load_dotenv
from solana.rpc.api import Client
from solders.keypair import Keypair
from solana.transaction import Transaction
from solders.system_program import TransferParams, transfer
from solders.pubkey import Pubkey

class TransactionExecutor:
    def __init__(self, rpc_url):
        load_dotenv()
        self.client = Client(rpc_url)
        self.trading_enabled = os.getenv("TRADING_ENABLED", "True").lower() == "true"
        self.dry_run = os.getenv("DRY_RUN", "False").lower() == "true"

        key_json = json.loads(os.getenv("PRIVATE_KEY_JSON"))
        self.keypair = Keypair.from_bytes(key_json)

    def execute_trade(self, action, amount):
        # For demo, we'll just transfer SOL to a dummy address
        # Replace this with actual DEX trade calls later
        if not self.trading_enabled:
            print(f"[Executor] Trading is disabled via config. Skipping execution.")
            return

        if self.dry_run:
            print(f"[Executor] DRY_RUN enabled -- Simulating {action} of {amount} SOL.")
            return

        # Dummy trade execution logic.
        dummy_recipient = Pubkey.from_string(os.getenv("DRY_RUN_RECIPIENT_WALLET"))

        # if action == 'BUY' or action == 'SELL':
        if self.dry_run:
            tx = Transaction().add(
                transfer(
                    TransferParams(
                        from_pubkey=self.keypair.pubkey(),
                        to_pubkey=dummy_recipient,
                        lamports=int(amount * 1e9) # SOL = 1e9 Lamports
                    )
                )
            )
        else:
            print(f"[Executor] Real trades are now handled by JupiterSwapper")

        response = self.client.send_transaction(tx, self.keypair)
        print(f"[Executor] Transaction submitted: {response}")
