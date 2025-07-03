# jkupiter_swapper.py

import requests
import base64
import os
import json
import traceback
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solders.transaction import VersionedTransaction as SoldersVTxn
from solders.keypair import Keypair as SoldersKeypair
from solders.message import to_bytes_versioned
from solders.pubkey import Pubkey
from spl.token.instructions import get_associated_token_address, create_associated_token_account
from spl.token.constants import TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID
from solders.account import Account
# from solders.program_id import ProgramId
# from solders.token import TokenAccountState
from solders.instruction import Instruction
# from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price


class JupiterSwapper:
    def __init__(self, executor):
        self.executor = executor
        self.client = Client(os.getenv("SOLANA_RPC_URL"))

        key_json = json.loads(os.getenv("PRIVATE_KEY_JSON"))
        self.wallet = SoldersKeypair.from_bytes(bytes(key_json))
        self.api_key = os.getenv("JUPITER_API_KEY")

        self.headers = {}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"


    async def execute_swap(self, token, decision):
        symbol = token['symbol']
        if decision['action'] != 'BUY':
            print(f"[JupyterSwapper] Skipping non-BUY action for {symbol}")
            return

        print(f"[JupyterSwapper] Preparing swap: SOL -> {symbol}")

        try:
            output_mint_pubkey = Pubkey(token["address"])
            user_pubkey = self.wallet.pubkey()

            # Pass token tags to ATA creation function
            destination_ata = await self._ensure_associated_token_account(
                output_mint_pubkey,
                user_pubkey,
                token_tags=token.get("tags")
            )

            quote_url = "https://lite-api.jup.ag/swap/v1/quote" #Before: quote_url = "https://quote-api.jup.ag/v6/quote"
            params = {
                "inputMint": 'So11111111111111111111111111111111111111112',
                "outputMint": token["address"],
                "amount": int(decision["amount"] * 1e9),
                "slippageBps": 50,
                "swapMode": 'ExactIn',
                "onlyDirectRoutes": "false",
                "restrictIntermediateTokens": "false"
            }

            quote_res = requests.get(quote_url, params=params)
            quote = quote_res.json()

            if "routePlan" not in quote:
                print(f"[JupyterSwapper] No valid swap routes. Response:\n{quote}")
                return

            # route = quote["routes"][0]
            route = {
                "routePlan": quote["routePlan"],
                "inputMint": quote["inputMint"],
                "inAmount": quote["inAmount"],
                "outputMint": quote["outputMint"],
                "outAmount": quote["outAmount"],
                "otherAmountThreshold": quote["otherAmountThreshold"],
                "swapMode": quote["swapMode"],
                "slippageBps": quote["slippageBps"],
                "platformFee": quote["platformFee"],
            }
            # print(quote)
            swap_url = "https://lite-api.jup.ag/swap/v1/swap" # Before: swap_url = "https://quote-api.jup.ag/v6/swap"
            swap_req = {
                "quoteResponse": quote,
                "userPublicKey": str(self.wallet.pubkey()),
                "wrapUnwrapSOL": True,
                "feeAccount": None,
                # optional optimisations
                "dynamicSlippage": True,
                "dynamicComputeUnitLimit": True,
                "prioritizationFeeLamports": {
                    "priorityLevelWithMaxLamports": {
                        "priorityLevel": "veryHigh",
                        "maxLamports": 1000000
                    }
                }
            }

            swap_data = requests.post(swap_url, json=swap_req).json()
            # print(f"[JupiterSwapper] Swap response:\n{swap_data}")

            if not swap_data.get("swapTransaction"):
                print("[JupiterSwapper] Swap transaction not received")
                return

            txn_bytes = base64.b64decode(swap_data["swapTransaction"])
            # txn = VersionedTransaction.deserialize(txn_bytes)
            txn = SoldersVTxn.from_bytes(txn_bytes)
            # Extract the message to sign
            msg_bytes = to_bytes_versioned(txn.message)
            # Sign the message bytes with wallet Keypair
            signed_txn = self.wallet.sign_message(msg_bytes)

            txn.signatures = [signed_txn]

            result = self.client.send_raw_transaction(
                bytes(txn), opts=TxOpts(skip_confirmation=False)
            )
            print(f"[JupiterSwapper] Swap submitted: {result}")

            return result.value

        except Exception as e:
            print("[JupiterSwapper] Failed with an unexpected error.")
            print(f"Type: {type(e)}")
            print(f"Args: {e.args}")
            print("Full traceback")
            traceback.print_exc()


    async def _get_mint_program_id(self, mint_address: Pubkey) -> Pubkey:
        """
        Fetches the Program ID that owns the given mint account.
        This determines if it's a legacy SPL token or SPL Token 2022
        """
        try:
            account_info = self.client.get_account_info(mint_address).value
            if account_info is None:
                raise ValueError(f"Mint account {mint_address} not found.")
            
            owner_program_id = account_info.owner
            print(f"[JupiterSwapper] Mint {mint_address} owned by program {owner_program_id}")
            return owner_program_id
        except Exception as e:
            print(f"[JupiterSwapper] Error fetching mint program ID for {mint_address}: {e}")
            return TOKEN_PROGRAM_ID

    
    async def _ensure_associated_token_account(self, mint_address: Pubkey, owner_address: Pubkey, token_tags: list = None) -> Pubkey: # Added token tags parameter
        """
        Ensures an associated token account exists for the given m int an owner,
        dynamically determining the correct SPL token Program ID.
        """

        # Determine the correct token program ID
        target_token_program_id = TOKEN_PROGRAM_ID # Default to legacy
        if token_tags and 'token-2022' in token_tags:
            target_token_program_id = TOKEN_2022_PROGRAM_ID
            print(f"[JupiterSwapper] Token {mint_address} identified as SPL Token 2022 via tags.")
        else:
            # If not tags provided or not token-2022 fetch from chain
            try:
                mint_owner_program_id = await self._get_mint_program_id(mint_address)
                if mint_owner_program_id == TOKEN_2022_PROGRAM_ID:
                    target_token_program_id = TOKEN_2022_PROGRAM_ID
                    print(f"[JupiterSwapper] Mint {mint_address} confirmed as SPL Token 2022 via on chain lookup.")
                else:
                    target_token_program_id = TOKEN_PROGRAM_ID
                    print(f"[JupiterSwapper] Mint {mint_address} confirmed as legacy SPL via on chain lookup.")
            except Exception as e:
                print(f"[JupiterSwapper] Could not confirm token program ID on-chain for {mint_address}, defaulting to legacy: {e}")
                target_token_program_id = TOKEN_PROGRAM_ID

        ata_address = get_associated_token_address(owner_address, mint_address, target_token_program_id)

        # Check if ATA already exists
        response = self.client.get_account_info(ata_address)
        if response.value is not None:
            # Check if the existing ATA is owned by the correct program ID
            if response.value.owner == target_token_program_id:
                print(f"[JupiterSwapper] ATA for {mint_address} already exists at {ata_address} (Correct Program)")
                return ata_address
            else:
                print(f"[JupiterSwapper] WARNING: ATA for {mint_address} exists at {ata_address} but owned by {response.value.owner} instead of {target_token_program_id}. This might cause issues.")
                pass
        
        print(f"[JupiterSwapper] Creating ATA for {mint_address} at {ata_address} with Program ID: {target_token_program_id}")

        # Create intruction for ATA
        create_ata_ix = create_associated_token_account(
            payer=owner_address,
            owner=owner_address,
            mint=mint_address,
            program_id=target_token_program_id
        )

        # Build and send the transaction to create ATA
        blockhash = self.client.get_latest_blockhash().value.blockhash
        create_ata_txn = SoldersVTxn.new(
            [create_ata_ix],
            blockhash,
            self.wallet.pubkey(),
            [self.wallet]
        )

        msg_bytes_ata = to_bytes_versioned(create_ata_txn.message)
        signed_txn_ata = self.wallet.sign_message(msg_bytes_ata)
        create_ata_txn.signatures = [signed_txn_ata]

        try:
            ata_creation_result = self.client.send_raw_transaction(
                bytes(create_ata_txn), opts=TxOpts(skip_confirmation=False, preflight_commitment="confirmed")
            )
            print(f"[JupiterSwapper] ATA creation submitted: {ata_creation_result.value}")
            # Wait for confirmation of ATA creation
            self.client.confirm_transaction(ata_creation_result.value, commitment="confirmed")
            print(f"[JupiterSwapper] ATA creation confirmed for: {mint_address}")
        except Exception as e:
            print(f"[JupiterSwapper] Failed to create ATA for {mint_address}: {e}")
            raise # Stop if fails

        return ata_address
