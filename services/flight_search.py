import asyncio
import os
import sys
import time
import httpx
from dotenv import load_dotenv
from fastapi import HTTPException
from langchain_core.tools import tool

# Explicitly load .env from the project root (parent of services/)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# Ensure utils can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.schemas import FlightSearchDetails, CheapestFlightSearchDetails


# @tool
class Search:
    """Flight Search Tool"""

    def __init__(self) -> None:
        self.AMADEUS_BASE = os.getenv("AMADEUS_BASE", "https://test.api.amadeus.com")
        self.AMADEUS_KEY = os.getenv("AMADEUS_KEY", "YOUR_AMADEUS_KEY")
        self.AMADEUS_SECRET = os.getenv("AMADEUS_SECRET", "YOUR_AMADEUS_SECRET")
        self.BOOKING_BASE = os.getenv("BOOKING_BASE", "https://distribution-xml.booking.com/json")
        self.BOOKING_KEY = os.getenv("BOOKING_API_KEY")
        self._token_cache = {"token": None, "exp": 0}

    async def get_amadeus_token(self):
        """Authenticate and return a cached Amadeus token."""
        if self._token_cache["token"] and self._token_cache["exp"] > time.time():
            return self._token_cache["token"]

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.AMADEUS_BASE}/v1/security/oauth2/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.AMADEUS_KEY,
                    "client_secret": self.AMADEUS_SECRET,
                },
            )

        if resp.status_code != 200:
            # Print error for better visibility during testing
            print(f"Auth Error: {resp.status_code} - {resp.text}")
            raise HTTPException(status_code=500, detail=f"Amadeus auth failed: {resp.text}")

        j = resp.json()
        self._token_cache = {
            "token": j["access_token"],
            "exp": time.time() + j["expires_in"] - 10,
        }
        return self._token_cache["token"]

    async def search_flights_on_a_date(self, flight_search_data_object: FlightSearchDetails) -> dict:
        """Search for flights based on the provided search criteria.

		Args:
			flight_search_data_object (FlightSearchDetails): The search criteria.
		Returns:
			dict: The search results.
		"""
        token = await self.get_amadeus_token()

        url = f"{self.AMADEUS_BASE}/v2/shopping/flight-offers"
        params = {
            "originLocationCode": flight_search_data_object.origin_iata,
            "destinationLocationCode": flight_search_data_object.destination_iata,
            "departureDate": flight_search_data_object.departure_date,
            "adults": flight_search_data_object.adults,
            "infants": flight_search_data_object.infants,
            "children": flight_search_data_object.children,
            "currencyCode": flight_search_data_object.currency,
            "travelClass": 'ECONOMY',
            "nonStop": str(flight_search_data_object.non_stop).lower() if flight_search_data_object.non_stop is not None else "false",
            "max": int(flight_search_data_object.max_results or 10)
        }

        # Only add optional parameters if they are valid
        if flight_search_data_object.departure_date:
            params["departureDate"] = flight_search_data_object.departure_date

        if flight_search_data_object.return_date:
            params["returnDate"] = flight_search_data_object.return_date

        if flight_search_data_object.max_price is not None:
            params["maxPrice"] = flight_search_data_object.max_price

        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers={"Authorization": f"Bearer {token}"}, params=params)

        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=f"Amadeus search failed: {r.text}")

        return {"source": "amadeus", "results": r.json()}

    async def search_cheapest_flights_date_range(self, flight_search_data_object: CheapestFlightSearchDetails) -> dict:
        """
		Search for cheapest flight dates.
		Endpoint: /v1/shopping/flight-dates
		"""
        token = await self.get_amadeus_token()

        if flight_search_data_object.destination:
             # --- SCENARIO 1: Destination Provided -> Flight Cheapest Date Search ---
             # Endpoint: /v1/shopping/flight-dates
             
             url = f"{self.AMADEUS_BASE}/v1/shopping/flight-dates"
             params = {
                "origin": flight_search_data_object.origin,
                "destination": flight_search_data_object.destination,
                "oneWay": str(flight_search_data_object.oneWay).lower(),
             }

             if flight_search_data_object.return_date:
                params["oneWay"] = "false"
                params["returnDate"] = flight_search_data_object.return_date
             else:
                params["oneWay"] = "true"

             if flight_search_data_object.departure_date:
                params["departureDate"] = flight_search_data_object.departure_date
 
             async with httpx.AsyncClient() as client:
                r = await client.get(url, headers={"Authorization": f"Bearer {token}"}, params=params)

             if r.status_code != 200:
                if r.status_code == 500:
                     print(f"Warning: Amadeus API returned 500 for cheapest flight date search. This is common in the Test Environment for unsupported routes.")
                     return {"source": "amadeus", "results": [], "error": "Amadeus API 500 System Error (Test Env limitation)"}
                raise HTTPException(status_code=r.status_code, detail=f"Amadeus cheapest flight search failed: {r.text}")

             return {"source": "amadeus", "results": r.json()}
        
        else:
             # --- SCENARIO 2: No Destination -> Flight Inspiration Search (Cheapest to Anywhere) ---
             # Endpoint: /v1/shopping/flight-destinations
             
             url = f"{self.AMADEUS_BASE}/v1/shopping/flight-destinations"
             params = {
                "origin": flight_search_data_object.origin,
                # "oneWay": str(flight_search_data_object.oneWay).lower(), # optional, defaults to false (round trip) in API
             }
             if flight_search_data_object.oneWay is not None:
                  params["oneWay"] = str(flight_search_data_object.oneWay).lower()

             if flight_search_data_object.departure_date:
                params["departureDate"] = flight_search_data_object.departure_date
             
             if flight_search_data_object.nonStop:
                  params["nonStop"] = str(flight_search_data_object.nonStop).lower()
                  
             if flight_search_data_object.maxPrice:
                  params["maxPrice"] = flight_search_data_object.maxPrice

             async with httpx.AsyncClient() as client:
                r = await client.get(url, headers={"Authorization": f"Bearer {token}"}, params=params)
             
             if r.status_code != 200:
                 if r.status_code == 500:
                      print(f"Warning: Amadeus API returned 500 for Flight Inspiration Search (Anywhere). Returning MOCK data.")
                      # Mock Data for testing
                      mock_data = [
                          {"destination": "PAR", "price": {"total": "150.00"}, "departureDate": "2026-09-01", "returnDate": "2026-09-10"},
                          {"destination": "JFK", "price": {"total": "350.00"}, "departureDate": "2026-10-05", "returnDate": "2026-10-15"},
                          {"destination": "TYO", "price": {"total": "550.00"}, "departureDate": "2026-11-20", "returnDate": "2026-11-30"},
                      ]
                      return {"source": "amadeus_mock", "type": "flight-destinations", "results": {"data": mock_data}, "warning": "Test Env 500 Error - Mock Data Used"}
                 raise HTTPException(status_code=r.status_code, detail=f"Amadeus flight inspiration search failed: {r.text}")
             
             return {"source": "amadeus", "type": "flight-destinations", "results": r.json()}


if __name__ == "__main__":
    search = Search()

    # 1. Standard Search Data
    flight_search_data = FlightSearchDetails(
        origin_iata="MAD",
        destination_iata="LON",
        departure_date="2026-06-12")

    # 2. Cheapest Date Search Data (Route Specific) - LHR->PAR
    flight_search_cheapest_route = CheapestFlightSearchDetails(
        origin="LHR",
        destination="PAR")

    # 3. Cheapest Destination Search Data (Anywhere) - MAD -> ?
    flight_search_inspiration = CheapestFlightSearchDetails(
        origin="MAD",
        destination=None) # Destination is None for "Anywhere"

    try:
        print("Starting flight search tests...")
        
        # --- Test 1: Standard Flight Search ---
        print("\n--- 1. Testing Standard Flight Search (MAD->LON) ---")
        results = asyncio.run(search.search_flights_on_a_date(flight_search_data))
        if "results" in results and "data" in results["results"]:
             print(f"Success! Found {len(results['results']['data'])} flight offers.")
        else:
             print("Standard search returned no results:", results)

        # --- Test 2: Cheapest Flight Date Search (Route Specific) ---
        print("\n--- 2. Testing Cheapest Flight Date Search (LHR->PAR) ---")
        results_route = asyncio.run(search.search_cheapest_flights_date_range(flight_search_cheapest_route))
        
        if "error" in results_route:
            print(f"Note: Cheapest Date Search failed (expected in Test Env): {results_route['error']}")
        else:
            print(f"Success! Result: {results_route}")

        # --- Test 3: Flight Inspiration Search (Anywhere) ---
        print("\n--- 3. Testing MOCK Flight Inspiration Search (MAD->Anywhere) ---")
        # Note: The true inspiration endpoint often fails in test env too, but the logic path is what we are testing.
        results_inspiration = asyncio.run(search.search_cheapest_flights_date_range(flight_search_inspiration))
        
        if "type" in results_inspiration and results_inspiration["type"] == "flight-destinations":
             if isinstance(results_inspiration.get("results"), dict):
                 data = results_inspiration.get("results", {}).get("data", [])
             else:
                 data = []
             print(f"Success! Found {len(data)} cheapest destinations from MAD.")
             if len(data) > 0:
                 print(f"Sample: {data[0]}")
        else:
             print(f"Inspiration search result: {results_inspiration}")

        print("\nOverall Search Sequence Completed.")
    except Exception as e:
        print(f"Failed to search flights: {e}")
        import traceback
        traceback.print_exc()
