import asyncio
import aiohttp
import sys


async def test_connectivity():
    url = "http://telegram-bot-api:8081"
    print(f"Testing connectivity to {url}...")
    try:

        async def fetch():
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return response.status, await response.text()

        status, text = await asyncio.wait_for(fetch(), timeout=5.0)
        print(f"Connection successful! Status: {status}")
        # The local API server returns some JSON or HTML at root
        return True
    except asyncio.TimeoutError:
        print("Connection timed out.")
    except Exception as e:
        print(f"Connection failed: {e}")
    return False


if __name__ == "__main__":
    if asyncio.run(test_connectivity()):
        sys.exit(0)
    else:
        sys.exit(1)
