import asyncio
import os
import sys
import time
import re
import httpx
from datetime import datetime
from dotenv import load_dotenv
try:
    from fastapi import HTTPException
except ImportError:
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str = None):
            self.status_code = status_code
            self.detail = detail
            super().__init__(f"{status_code}: {detail}")
# from langchain_core.tools import tool

# Explicitly load .env from the project root (parent of services/)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# Ensure utils can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Optional
from utils.schemas import FlightSearchQueryDetails, SortBy


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
        """
        Search for flights matching specific criteria on a given date.
        
        This method performs a standard flight search using the Amadeus Flight Offers Search API.
        It supports filtering by origin, destination, date, passengers, class, etc.
        
        Args:
            flight_search_query_object (FlightSearchQueryDetails): Object containing search parameters.
            
        Returns:
            dict: Raw dictionary response from the Amadeus API containing flight offers.
        """
        token = await self.get_amadeus_token()
        url = f"{self.AMADEUS_BASE}/v2/shopping/flight-offers"
        
        # Base parameters
        params = {
            "originLocationCode": flight_search_query_object.origin_iata,
            "destinationLocationCode": flight_search_query_object.destination_iata,
            "departureDate": flight_search_query_object.departure_date,
            "adults": flight_search_query_object.adults,
            "currencyCode": flight_search_query_object.currency,
            "max": int(flight_search_query_object.max_results or 5)
        }
        
        # Optional params
        if flight_search_query_object.return_date:
            params["returnDate"] = flight_search_query_object.return_date
        if flight_search_query_object.travel_class:
            params["travelClass"] = flight_search_query_object.travel_class
        if flight_search_query_object.non_stop:
            params["nonStop"] = "true"

        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers={"Authorization": f"Bearer {token}"}, params=params)

        if r.status_code != 200:
             raise HTTPException(status_code=r.status_code, detail=f"Amadeus search failed: {r.text}")

        return {"source": "amadeus", "results": r.json()}

    async def search_flights_advanced(
        self,
        flight_search_data_object: FlightSearchQueryDetails,
        sort_by: Optional[SortBy] = SortBy.PRICE,
        max_stops: Optional[int] = 2,
        min_bookable_seats: Optional[int] = 1,
        instant_ticketing_required: Optional[bool] = None,
        max_results: Optional[int] = 10
    ) -> dict:
        """
        Perform an advanced flight search with client-side filtering and sorting.
        
        Args:
            flight_search_data_object (FlightSearchQueryDetails): Base search criteria.
            sort_by (Optional[SortBy]): Sorting criteria (overrides object).
                Possible values: "price", "duration", "generated_departure_time", "generated_arrival_time", "number_of_bookable_seats", "last_ticketing_date".
            max_stops (Optional[int]): Max stops filter (overrides object).
            min_bookable_seats (Optional[int]): Min seats filter (overrides object).
            instant_ticketing_required (Optional[bool]): Instant ticketing filter (overrides object).
            max_results (Optional[int]): Max results to return (default 10).
        
        Returns:
            dict: Search results.
        """
        token = await self.get_amadeus_token()
        url = f"{self.AMADEUS_BASE}/v2/shopping/flight-offers"
        
        # 1. Map Inputs to Params
        params = {}
        query_obj = flight_search_data_object
        
        params["originLocationCode"] = query_obj.origin_iata
        params["destinationLocationCode"] = query_obj.destination_iata
        params["departureDate"] = query_obj.departure_date
        params["adults"] = query_obj.adults
        params["currencyCode"] = query_obj.currency
        params["max"] = int(max_results or query_obj.max_results or 10)
        if query_obj.return_date:
            params["returnDate"] = query_obj.return_date
        if query_obj.travel_class:
            params["travelClass"] = query_obj.travel_class
        if query_obj.non_stop:
            params["nonStop"] = "true"
        if query_obj.included_airlines:
            params["includedAirlineCodes"] = ",".join(query_obj.included_airlines)
        if query_obj.excluded_airlines:
            params["excludedAirlineCodes"] = ",".join(query_obj.excluded_airlines)
        if query_obj.max_price:
            params["maxPrice"] = int(query_obj.max_price)

        # Execute Request
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers={"Authorization": f"Bearer {token}"}, params=params)

        if r.status_code != 200:
            if r.status_code == 500:
                 return {"source": "amadeus", "results": [], "error": "Amadeus API 500 System Error"}
            raise HTTPException(status_code=r.status_code, detail=f"Amadeus search failed: {r.text}")

        data = r.json()
        results = data.get("data", [])
        
        # --- Client Side Processing ---
        
        # Extract filtering criteria (Argument > Object)
        _max_stops = max_stops if max_stops is not None else getattr(query_obj, 'max_stops', None)
        _min_seats = min_bookable_seats if min_bookable_seats is not None else getattr(query_obj, 'min_bookable_seats', None)
        _instant_ticketing = instant_ticketing_required if instant_ticketing_required is not None else getattr(query_obj, 'instant_ticketing_required', False)
        _sort_by = sort_by if sort_by is not None else getattr(query_obj, 'sort_by', None)

        # 1. Apply Filters
        if (_max_stops is not None and _max_stops > 0) or _min_seats or _instant_ticketing:
            filtered_results = []
            for offer in results:
                valid = True
                
                # Filter: Min Bookable Seats
                if _min_seats:
                    if int(offer.get("numberOfBookableSeats", 0)) < _min_seats:
                        valid = False

                # Filter: Instant Ticketing Required
                if valid and _instant_ticketing:
                    if not offer.get("instantTicketingRequired", False):
                        valid = False

                # Filter: Max Stops (if > 0)
                if valid and _max_stops is not None and _max_stops > 0:
                    for itinerary in offer.get("itineraries", []):
                        stops = len(itinerary.get("segments", [])) - 1
                        if stops > _max_stops:
                            valid = False
                            break
                            
                if valid:
                    filtered_results.append(offer)
            results = filtered_results

        # 2. Sorting
        if _sort_by == SortBy.DEPARTURE_TIME:
            def get_dep_time(offer):
                try: return offer["itineraries"][0]["segments"][0]["departure"]["at"]
                except: return "9999-12-31"
            results.sort(key=get_dep_time)
        elif _sort_by == SortBy.ARRIVAL_TIME:
             def get_arr_time(offer):
                try: return offer["itineraries"][0]["segments"][-1]["arrival"]["at"]
                except: return "9999-12-31"
             results.sort(key=get_arr_time)
        elif _sort_by == SortBy.DURATION:
             def get_duration(offer):
                try: return self._parse_duration(offer["itineraries"][0]["duration"])
                except: return 999999
             results.sort(key=get_duration)
        elif _sort_by == SortBy.PRICE:
             def get_price(offer):
                try: return float(offer["price"]["total"])
                except: return 0.0
             results.sort(key=get_price)
        elif _sort_by == SortBy.SEATS:
             def get_seats(offer):
                try: return int(offer.get("numberOfBookableSeats", 0))
                except: return 0
             results.sort(key=get_seats, reverse=True) # Descending (more seats first)
        elif _sort_by == SortBy.LAST_TICKETING_DATE:
             def get_ltd(offer):
                return offer.get("lastTicketingDate", "9999-12-31")
             results.sort(key=get_ltd) # Ascending (earlier deadline first)
        
        data["data"] = results
        return {"source": "amadeus", "results": data}


if __name__ == "__main__":
    search = Search()

    # 1. Standard Search (Simple)
    print("\n--- 1. Testing Standard Search (MAD->LON) ---")
    flight_search_data = FlightSearchQueryDetails(
        origin_iata="MAD",
        destination_iata="LON",
        departure_date="2026-06-12",
        max_results=5
    )
    try:
        results = asyncio.run(search.search_flights_on_a_date(flight_search_data))
        print(f"Found {len(results.get('results', {}).get('data', []))} offers.")
    except Exception as e:
        print(f"Search failed: {e}")

    # 2. Testing Advanced Search (With client sort)
    print("\n--- 2. Testing Advanced Search (MAD->LON, Sort: DURATION) ---")
    flight_search_data_adv = FlightSearchQueryDetails(
        origin_iata="MAD",
        destination_iata="LON",
        departure_date="2026-06-12",
        max_results=5,
        sort_by=SortBy.DURATION
    )
    try:
        results = asyncio.run(search.search_flights_advanced(flight_search_data_adv))
        offers = results.get("results", {}).get("data", [])
        print(f"Found {len(offers)} offers.")
        if offers:
            print(f"Top result duration: {offers[0]['itineraries'][0]['duration']}")
    except Exception as e:
        print(e)

    # 3. Testing New Filters/Sorts
    print("\n--- 3. Testing Sort by SEATS and Min Seats Filter ---")
    flight_search_data_seats = FlightSearchQueryDetails(
         origin_iata="MAD",
         destination_iata="LON",
         departure_date="2026-06-12",
         max_results=10,
         sort_by=SortBy.SEATS,
         min_bookable_seats=3
    )
    try:
        results = asyncio.run(search.search_flights_advanced(flight_search_data_seats))
        offers = results.get("results", {}).get("data", [])
        print(f"Found {len(offers)} offers with >= 3 seats.")
        for i, off in enumerate(offers[:3]):
             print(f"Rank {i+1}: {off.get('numberOfBookableSeats')} seats")
    except Exception as e:
        print(e)
