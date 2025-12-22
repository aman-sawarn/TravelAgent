
import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv

# Explicitly load .env from the project root
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path)

# Ensure utils can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.flight_search import Search

async def test_inspiration_endpoint():
    search = Search()
    token = await search.get_amadeus_token()
    base_url = "https://test.api.amadeus.com/v1/shopping/flight-destinations"
    
    test_cases = [
        {"origin": "MAD"},
        {"origin": "MAD", "oneWay": "false"},
        {"origin": "MAD", "oneWay": "true"},
        {"origin": "PAR"},
        {"origin": "LON"},
        {"origin": "JFK"},
        {"origin": "BOS"} # Boston is often used in Amadeus examples
    ]

    print(f"Testing Flight Inspiration API: {base_url}\n")

    async with httpx.AsyncClient() as client:
        for params in test_cases:
            print(f"Testing params: {params}")
            try:
                r = await client.get(base_url, headers={"Authorization": f"Bearer {token}"}, params=params)
                print(f"Status: {r.status_code}")
                if r.status_code == 200:
                    print("SUCCESS! Data found.")
                    # print(r.json())
                    break # Found a working case!
                else:
                    print(f"Error: {r.text}")
            except Exception as e:
                print(f"Exception: {e}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_inspiration_endpoint())
