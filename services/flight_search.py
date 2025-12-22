import asyncio
import os
import sys
import time
import re
import httpx
from datetime import datetime
from dotenv import load_dotenv
from fastapi import HTTPException
from langchain_core.tools import tool

# Explicitly load .env from the project root (parent of services/)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# Ensure utils can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.schemas import FlightSearchQueryDetails, CheapestFlightSearchDetails, SortBy


# @tool
class Search:
    """Flight Search Tool"""

    def __init__(self) -> None:
        self.AMADEUS_BASE = os.getenv("AMADEUS_BASE", "https://test.api.amadeus.com")
        self.AMADEUS_KEY = os.getenv("AMADEUS_KEY", "YOUR_AMADEUS_KEY")
        self.AMADEUS_SECRET = os.getenv("AMADEUS_SECRET", "YOUR_AMADEUS_SECRET")
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

    def _parse_duration(self, duration_str: str) -> int:
        """Parse PTxxHxxM format to minutes."""
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', duration_str)
        if not match:
            return 0
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        return hours * 60 + minutes

    async def search_flights_on_a_date(self, flight_search_query_object: FlightSearchQueryDetails) -> dict:
        """Search for flights based on the provided search criteria.

        Args:
            flight_search_query_object (FlightSearchQueryDetails): The search criteria.
        Returns:
            dict: The search results.
        """
        token = await self.get_amadeus_token()

        url = f"{self.AMADEUS_BASE}/v2/shopping/flight-offers"
        
        # Base parameters
        params = {
            "originLocationCode": flight_search_query_object.origin_iata,
            "destinationLocationCode": flight_search_query_object.destination_iata,
            "departureDate": flight_search_query_object.departure_date,
            "adults": flight_search_query_object.adults,
            "infants": flight_search_query_object.infants,
            "children": flight_search_query_object.children,
            "currencyCode": flight_search_query_object.currency,
            "travelClass": flight_search_query_object.travel_class or 'ECONOMY',
            "max": int(flight_search_query_object.max_results or 5)
        }

        # --- Filtering Parameters ---
        
        # Stops
        if flight_search_query_object.non_stop:
            params["nonStop"] = "true"
        elif flight_search_query_object.max_stops == 0:
            params["nonStop"] = "true"
        else:
            params["nonStop"] = "false"

        # Airlines
        if flight_search_query_object.included_airlines:
            params["includedAirlineCodes"] = ",".join(flight_search_query_object.included_airlines)
        
        if flight_search_query_object.excluded_airlines:
            params["excludedAirlineCodes"] = ",".join(flight_search_query_object.excluded_airlines)

        # Optional Dates / Price
        if flight_search_query_object.return_date:
            params["returnDate"] = flight_search_query_object.return_date

        if flight_search_query_object.max_price is not None:
            params["maxPrice"] = int(flight_search_query_object.max_price)

        # --- Sorting (API side) ---
        # Amadeus supports 'price', 'duration', 'carrier', 'segments'
        # NOTE: Test API seems to reject 'sort' param with 400 in some cases. 
        # Switching to client-side sorting for robustness.
        # if flight_search_data_object.sort_by == SortBy.PRICE:
        #     params["sort"] = "price"
        # elif flight_search_data_object.sort_by == SortBy.DURATION:
        #     params["sort"] = "duration"
        
        # Execute Request
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers={"Authorization": f"Bearer {token}"}, params=params)

        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=f"Amadeus search failed: {r.text}")

        data = r.json()
        results = data.get("data", [])

        # --- Post-Processing (Client Side) ---

        # 1. Filter by max_stops (if > 0, since API only handles boolean nonStop)
        if flight_search_query_object.max_stops is not None and flight_search_query_object.max_stops > 0:
            filtered_results = []
            for offer in results:
                valid = True
                for itinerary in offer.get("itineraries", []):
                    # Segments - 1 = Stops
                    stops = len(itinerary.get("segments", [])) - 1
                    if stops > flight_search_query_object.max_stops:
                        valid = False
                        break
                if valid:
                    filtered_results.append(offer)
            results = filtered_results

        # 2. Sort by other criteria
        if flight_search_query_object.sort_by == SortBy.DEPARTURE_TIME:
            # Sort by first segment departure of first itinerary
            def get_dep_time(offer):
                try:
                    return offer["itineraries"][0]["segments"][0]["departure"]["at"]
                except (KeyError, IndexError):
                    return "9999-12-31" # Push to end if missing
            results.sort(key=get_dep_time)
        
        elif flight_search_query_object.sort_by == SortBy.ARRIVAL_TIME:
            # Sort by last segment arrival of first itinerary works for O&D
            def get_arr_time(offer):
                try:
                    return offer["itineraries"][0]["segments"][-1]["arrival"]["at"]
                except (KeyError, IndexError):
                    return "9999-12-31"
            results.sort(key=get_arr_time)
            
        elif flight_search_query_object.sort_by == SortBy.DURATION:
            # Client side duration sort
            def get_duration(offer):
                try:
                    return self._parse_duration(offer["itineraries"][0]["duration"])
                except (KeyError, IndexError):
                    return 999999
            results.sort(key=get_duration)
            
        elif flight_search_query_object.sort_by == SortBy.PRICE:
            # Client side price sort (usually default, but ensure it)
            def get_price(offer):
                try:
                    return float(offer["price"]["total"])
                except (KeyError, ValueError):
                    return 0.0
            results.sort(key=get_price)

        # Update data with processed results
        data["data"] = results

        return {"source": "amadeus", "results": data}

    async def search_cheapest_flights_date_range(self, flight_search_data_object: CheapestFlightSearchDetails) -> dict:
        """
        Search for cheapest flight dates.
        Endpoint: /v1/shopping/flight-dates
        """
        token = await self.get_amadeus_token()
            
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
                # Return empty list to avoid crashing logic, let agent handle "no inspiration found"
                return {"source": "amadeus", "results": [], "error": "Amadeus API 500 System Error (Test Env limitation)"}
            raise HTTPException(status_code=r.status_code, detail=f"Amadeus cheapest flight search failed: {r.text}")

        return {"source": "amadeus", "results": r.json()}


if __name__ == "__main__":
    search = Search()

    # 1. Standard Search Data (Testing Filters)
    print("\n--- 1. Testing Filtered Search (MAD->LON, Sort: DURATION) ---")
    flight_search_data = FlightSearchQueryDetails(
        origin_iata="MAD",
        destination_iata="LON",
        departure_date="2026-06-12",
        max_results=5,
        sort_by=SortBy.DURATION
    )
    
    try:
        results = asyncio.run(search.search_flights_on_a_date(flight_search_data))
        offers = results.get("results", {}).get("data", [])
        print(f"Found {len(offers)} offers.")
        if offers:
            print(f"Top result duration: {offers[0]['itineraries'][0]['duration']}")
            print(f"Top result price: {offers[0]['price']['total']}")
    except Exception as e:
        print(f"Search failed: {e}")
        import traceback
        traceback.print_exc()

    time.sleep(2) # Avoid Rate Limits

    # 2. Testing Client Side Sort (Departure Time)
    print("\n--- 2. Testing Sort by Departure Time ---")
    flight_search_data_dep = FlightSearchQueryDetails(
        origin_iata="MAD",
        destination_iata="LON",
        departure_date="2026-06-12",
        max_results=5,
        sort_by=SortBy.DEPARTURE_TIME
    )
    try:
        results = asyncio.run(search.search_flights_on_a_date(flight_search_data_dep))
        offers = results.get("results", {}).get("data", [])
        print(f"Found {len(offers)} offers.")
        for i, off in enumerate(offers[:3]):
             dep = off['itineraries'][0]['segments'][0]['departure']['at']
             print(f"Rank {i+1}: {dep}")
    except Exception as e:
        print(e)
