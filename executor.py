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

        key_json = json.loads(os.getenv("PRIVATE_KEY_JSON"))

        self.keypair = Keypair.from_bytes(key_json)

    def execute_trade(self, action, amount):
        # For demo, we'll just transfer SOL to a dummy address
        # Replace this with actual DEX trade calls later

        dummy_recipient = Pubkey.from_string("3Vk5TtQXeirGG1BpwyCxH489H76yp1en3Au1fLZ1PPc1")

        if action == 'BUY' or action == 'SELL':
            tx = Transaction().add(
                transfer(
                    TransferParams(
                        from_pubkey=self.keypair.pubkey(),
                        to_pubkey=dummy_recipient,
                        lamports=int(amount * 1e9) # SOL = 1e9 Lamports
                    )
                )
            )

            response = self.client.send_transaction(tx, self.keypair)
            print(f"[Executor] Transaction submitted: {response}")

