from solana.rpc.api import Client
# from solana.rpc.websocket_api import SolanaWsClient
from solana.rpc.commitment import Commitment
import asyncio
import json
import httpx # For asynchronous HTTP requests to external AI agents
from dotenv import load_dotenv
import os

load_dotenv()

# Configuration
RPC_URL = os.getenv("RPC_URL")
WS_URL = os.getenv("WS_URL")
# To-define Agent No. 1
EXTERNAL_AI_AGENT_API_URL = os.getenv("EXTERNAL_AI_AGENT_API_URL")
EXTERNAL_AI_AGENT_API_KEY = os.getenv("EXTERNAL_AI_AGENT_API_KEY")

async def send_data_to_ai_agent(data: dict):
    """
        Send Processed data to an external AI agent API.
    """
    headers = {"authorization":f"Bearer {EXTERNAL_AI_AGENT_API_KEY}",
    "Content-Type": "application/json"}
    async with hhtpx.AsyncClient() as client:
        try:
            print(f"Sending data to AI agent: {json.dumps(data)}")
            response = await client.post(
                EXTERNAL_AI_AGENT_API_URL, 
                json=data, 
                headers = headers,
                timeout = 10.0           
            )
            response.raise_for_status()
            # Raise an exception for 4XX or 5XX status codes
            print(f"AI Agent Response: {response.json()}")
            return response.json()
        except httpx.RequestError as exc:
            print(f"An error occurred while requesting {exc.request.url!r}: {exc}")
            return None
        except httpx.HTTPStatusError as exc:
            print(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc.response.text}")
            return None

async def process_block_data(block_data: dict):
    """
        Processes block data and prepares it for an external AI agent.
        In a real scenario, this would involve more sophisticated parsing and feaure engineering.
    """
    # Example: Extracting a simplified view of transactions from the block
    transactions_summary = []
    if 'transactions' in block_data:
        for tx in block_data["transactions"]:
            # Only process if transaction is successful and has meta data
            if not tx['meta']['err'] and tx['meta']:
                signaures = tx['transaction']['signatures']
                if signatures:
                    transactions_summary.append({
                        'signature': signatures[0],
                        'fee': tx['meta']['fee'],
                        'log_messages': tx['meta']['logMessages']
                    })
    # Prepare data for the AI agent. This format is highly dependent on the agent's API.
    data_for_agent = {
        'slot': block_data['parentSlot'] + 1,
        'blockhash': block_data['blockhash'],
        'timestamp': block_data['blockTime'],
        'transaction_count': len(transactions_summary),
        'transactions_summary': transactions_summary
    }

    # Send this processed data to the external AI agent
    await send_data_to_ai_agent(data_for_agent)
    
async def subscribe_to_new_blocks():
    """
    Subscribes to new blocks via Websocket and processes block data.
    """
    print(f"Connecting to WebSocket: {WS_URL}")
    async with SolanaWsClient(WS_URL) as ws:
        await ws.block_subscribe(
            commitment=Commitment("finalized"),
            encoding="json", # Request JSON encoding for easier parsing
            transaction_details="full", # Request full transaction details
            rewards=False,
            max_supported_transaction_version=0
        )
        print("Subscribed to new blocks. Waiting for messages...")
        async for msg in ws:
            if 'result' in msg and 'value' in msg['result'] and 'block' in msg['result']['value']:
                block_data = msg['result']['value']['block']
                print(f"Received Block: Slot {block_data['parentSlot'] + 1}")
                await process_block_data(block_data)

async def get_recent_transactions_and_send_to_agent(num_transactions=5):
    """
    Fetches recent confirmed transactions using HTTP and sends to AI agent.
    """
    print(f"Connecting to RPC: {RPC_URL}")
    client = Client(RPC_URL)

    print(f"Fetching {num_transactions} recent confirmed signatures...")
    response = client.get_signatures_for_address(
        'Vote11111111111111111111111111111111',
        limit=num_transactions,
        commitment=Commitment('confirmed')
    )

    if response.value:
        print("Recent Transaction Signatures:")
        for signature_info in response.value:
            signature = signature_info.signature
            print(f" Signature: {signature}")
            # Fetch full transaction details if needed
            tx_details = client.get_transaction(
                signature, 
                commitment=Commitment('confirmed'),
                encoding="json",
                max_supported_transaction_version=0
            )
            if tx_details.value:
                # Prepare and send historical transaction data to AI agent
                await send_data_to_ai_agent({
                    'type': 'historical_transaction',
                    'signature': signature,
                    'details': tx_details.value
                })
            else:
                print(f" Could not fetch details for {signature}")
    else:
        print("No recent transactions found or an error occurred.")

async def main():
    # Run both functions concurrently
    await asyncio.gather(
        # subscribe_to_new_blocks(),
        get_recent_transactions_and_send_to_agent()
    )

if __name__ == "__main__":
    # Note: Running both concurrenly in a simple script might lead to interleaved output.
    # For a real application, these would be separate services or processes.
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting.")





