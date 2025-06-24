import pandas as pd
import httpx
# For making asynchronous HTTP requests to external agents
import asyncio

# Configuration
EXTERNAL_INDICATOR_API_URL = "https://api.example.com/indicators/calculate" # Placeholder for external indicator API
EXTERNAL_INDICATOR_API_KEY = "INDICATOR-API-KEY"
# Securely loaded API key

async def get_indicators_from_external_api(ohlcv_data: dict) -> dict:
    """
        Sends OHLCV to an exernal indicator API and returns
        calculated indicators.
    """
    headers = {"Auhorization": f"Bearer {EXTERNAL_INDICATOR_API_KEY}",
    "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        try:
            print(f"Sending OHLCV data to external indicator API...")
            response await client.post(EXTERNAL_INDICATOR_API_URL, json=oclcv_data, headers=headers, timeout=15.0)
            response.raise_for_status()
            # Raise and exception for 4xx or 5xx status codes
            return response.json()
        except httpx.RequestError as exc:
            print(f"An error occurred while requesting {exc.request.url!r}:{exc}")
            return {"error": str(exc)}
        except httpx.HTTPStatusError as exc:
            print(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc.response.text}")
            return {"error": exc.response.text}

async def main():
    # Example Usage: Prepare sample OHLCV data to send o the external API
    # in a real scenario, this data would come from your data extraction pipeline
    ohlcv_data = {
        "symbol": "SOL/USDC",
        "interval": "1h",
        "data": [
            {"timestamp": "2023-01-01T00:00:00Z", "open": 100, "high": 103, "low": 99, "close": 102, "volume": 1000},
            {"timestamp": "2023-01-01T01:00:00Z", "open": 102, "high": 104, "low": 101, "close": 101, "volume": 1200},
            {"timestamp": "2023-01-01T02:00:00Z", "open": 101, "high": 105, "low": 100, "close": 104, "volume": 1100},
            {"timestamp": "2023-01-01T03:00:00Z", "open": 104, "high": 106, "low": 103, "close": 103, "volume": 1300},
            {"timestamp": "2023-01-01T04:00:00Z", "open": 103, "high": 105, "low": 102, "close": 105, "volume": 1500},
            {"timestamp": "2023-01-01T05:00:00Z", "open": 105, "high": 108, "low": 104, "close": 107, "volume": 1400},
            {"timestamp": "2023-01-01T06:00:00Z", "open": 107, "high": 110, "low": 106, "close": 106, "volume": 1600},
            {"timestamp": "2023-01-01T07:00:00Z", "open": 106, "high": 109, "low": 105, "close": 108, "volume": 1700},
            {"timestamp": "2023-01-01T08:00:00Z", "open": 108, "high": 111, "low": 107, "close": 110, "volume": 1800},
            {"timestamp": "2023-01-01T09:00:00Z", "open": 110, "high": 112, "low": 109, "close": 111, "volume": 1900},
            {"timestamp": "2023-01-01T10:00:00Z", "open": 111, "high": 114, "low": 110, "close": 113, "volume": 2000},
            {"timestamp": "2023-01-01T11:00:00Z", "open": 113, "high": 115, "low": 111, "close": 112, "volume": 2100},
            {"timestamp": "2023-01-01T12:00:00Z", "open": 112, "high": 115, "low": 113, "close": 114, "volume": 2200},
            {"timestamp": "2023-01-01T13:00:00Z", "open": 114, "high": 117, "low": 113, "close": 116, "volume": 2300},
            {"timestamp": "2023-01-01T14:00:00Z", "open": 116, "high": 118, "low": 114, "close": 115, "volume": 2400},
            {"timestamp": "2023-01-01T15:00:00Z", "open": 115, "high": 118, "low": 116, "close": 117, "volume": 2500},
            {"timestamp": "2023-01-01T16:00:00Z", "open": 117, "high": 120, "low": 116, "close": 119, "volume": 2600},
            {"timestamp": "2023-01-01T17:00:00Z", "open": 119, "high": 119, "low": 117, "close": 118, "volume": 2700},
            {"timestamp": "2023-01-01T18:00:00Z", "open": 118, "high": 121, "low": 119, "close": 120, "volume": 2800},
            {"timestamp": "2023-01-01T19:00:00Z", "open": 120, "high": 122, "low": 121, "close": 121, "volume": 2900}
        ]
    }

    print("Requesting indicators from external API...")
    indicators = await get_indicators_from_exernal_api(ohlcv_data)

    if indicators and "error" not in indicators:
        print("Calculated Indicators from External API:")
        # Assuming the external API returns a structure like:
        # {"SMA_10": [...], "RSI_14": [...], ...}
        print(pd.DataFrame(indicators).tail())
        else:
            print("Failed to retrieve indicators from external API.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting.")