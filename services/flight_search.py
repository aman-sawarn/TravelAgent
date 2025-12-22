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
            "nonStop": False,
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
        print("params : ", params)
        print("url : ", url)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=f"Amadeus search failed: {r.text}")

        return {"source": "amadeus", "results": r.json()}

    async def search_cheapest_flights_date_range(self, flight_search_data_object: CheapestFlightSearchDetails) -> dict:
        """
		Search for cheapest flight dates.
		Endpoint: /v1/shopping/flight-dates
		"""
        token = await self.get_amadeus_token()

        url = f"{self.AMADEUS_BASE}/shopping/flight-dates"
        params = {
            "origin": flight_search_data_object.origin,
            "destination": flight_search_data_object.destination,
            "oneWay": flight_search_data_object.oneWay,
        }

        if flight_search_data_object.return_date:
            params["oneWay"] = False
            params["returnDate"] = flight_search_data_object.return_date
        else:
            params["oneWay"] = True

        if flight_search_data_object.departure_date:
            params["departureDate"] = flight_search_data_object.departure_date

        print("params : ", params)
        print("url : ", url)
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers={"Authorization": f"Bearer {token}"}, params=params)

        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=f"Amadeus cheapest flight search failed: {r.text}")

        return {"source": "amadeus", "results": r.json()}


if __name__ == "__main__":
    search = Search()
    # flight_search_data = FlightSearchDetails(
    #     origin_iata="MAD",
    #     destination_iata="LON",
    #     departure_date="2026-03-12")

    flight_search_cheapest_data = CheapestFlightSearchDetails(
        origin="BOM",
        destination="DEL")
    try:
        print("Starting flight search...")
        # print("Flight Search Data:", flight_search_data)
        print("*=" * 20)
        # results = asyncio.run(search.search_flights_on_a_date(flight_search_data))
        print("flight_search_cheapest_data : ",flight_search_cheapest_data)
        results = asyncio.run(search.search_cheapest_flights_date_range(flight_search_cheapest_data))
        print(results)
        print("Search successful!")
    except Exception as e:
        print(f"Failed to search flights: {e}")
