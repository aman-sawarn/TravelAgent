
import asyncio
import os
import sys
# Explicitly load .env from the project root
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path)

# Ensure utils can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.environment import Actuator, CheapestFlightSearchDetails

async def test_routes():
    search = Actuator()
    routes = [
        ("MAD", "MUC"),
        ("LHR", "JFK"),
        ("PAR", "NYC"),
        ("MAD", "NYC"),
        ("LON", "PAR"),
        ("BOM", "DEL"),
        ("SFO", "JFK")
    ]
    
    print("Testing routes for Cheapest Flight Dates endpoint...")
    for origin, dest in routes:
        print(f"\nTesting {origin} -> {dest}")
        details = CheapestFlightSearchDetails(origin=origin, destination=dest)
        try:
            # We need to call the method. 
            # Note: The current implementation in environment.py might catch the 500 and return an error dict.
            # We want to see if any return actual results.
            result = await search.search_cheapest_flights_date_range(details)
            if "error" in result:
                print(f"FAILED: {result['error']}")
            else:
                print(f"SUCCESS! Found {len(result.get('data', []))} results.")
                print(result)
                break
        except Exception as e:
            print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    asyncio.run(test_routes())
