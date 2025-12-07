import asyncio
import os
import sys
import time
import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

# Explicitly load .env from the project root (parent of services/)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# Ensure utils can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.schemas import FetchedFlightSearchDetails


class Search:
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

    async def search_flights_on_a_date(self, flight_search_data_object: FetchedFlightSearchDetails) -> dict:
        """Search for flights based on the provided search criteria.

        Args:
            flight_search_data_object (FetchedFlightSearchDetails): The search criteria.
            FetchedFlightSearchDetails: The search criteria.
                origin_iata (str): The origin airport IATA code.
                destination_iata (str): The destination airport IATA code.
                departure_date (str): The departure date in YYYY-MM-DD format.
                adults (int): The number of adults.
                infants (int): The number of infants.
                children (int): The number of children.
                currency (str): The currency code.
                max_results (int): The maximum number of results to return.
                return_date (str, optional): The return date in YYYY-MM-DD format.
                max_price (float, optional): The maximum price.
        Returns:.
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
            "nonStop": False,
            "max": int(flight_search_data_object.max_results)
        }

        # Only add optional parameters if they are valid
        if flight_search_data_object.return_date:
            params["returnDate"] = flight_search_data_object.return_date

        if flight_search_data_object.max_price is not None:
            params["maxPrice"] = flight_search_data_object.max_price

        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers={"Authorization": f"Bearer {token}"}, params=params)

        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=f"Amadeus search failed: {r.text}")

        return {"source": "amadeus", "results": r.json()}

    async def search_cheapest_flights_on_a_date_range(self, flight_search_data_object: FetchedFlightSearchDetails) -> dict:
        """
        Search for cheapest flight dates.
        Endpoint: /v1/shopping/flight-dates
        """
        token = await self.get_amadeus_token()

        url = f"{self.AMADEUS_BASE}/v1/shopping/flight-dates"
        params = {
            "origin": flight_search_data_object.origin_iata,
            "destination": flight_search_data_object.destination_iata,
            # 'oneWay': 'true' if no return date? Default seems to be false (round trip) if 'duration' provided, or maybe just list dates.
            # API docs say: either oneWay=true OR duration (comma separated list of days)
        }
        
        # If no return date is provided, we assume one-way for simplicity unless logic dictates otherwise
        if not flight_search_data_object.return_date:
            params["oneWay"] = "true"
        # else:
            # If return date is provided, usually flight-dates expects 'duration' (length of stay), not a specific return date.
            # For now, let's keep it simple. If the user wants specific dates, they use flight-offers.
            # flight-dates is usually "I want to go roughly around this time, what days are cheap?"
            
        # Optional: View-window (if supported) or just rely on default (future dates)
        
        # Add filtering if available
        if flight_search_data_object.non_stop:
            params["nonStop"] = "true"

        if flight_search_data_object.max_price is not None:
            params["maxPrice"] = int(flight_search_data_object.max_price)

        # Execute request
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers={"Authorization": f"Bearer {token}"}, params=params)

        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=f"Amadeus search failed: {r.text}")

        return {"source": "amadeus", "results": r.json()}


if __name__ == "__main__":
    search = Search()
    flight_search_data = FetchedFlightSearchDetails(
        origin_iata="MAD",
        destination_iata="LON",
        departure_date="2025-05-12")
        
    try:
        print("Starting flight search...")
        results = asyncio.run(search.search_cheapest_flights_on_a_date_range(flight_search_data))
        print(results)
        print("Search successful!")
    except Exception as e:
        print(f"Failed to search flights: {e}")
