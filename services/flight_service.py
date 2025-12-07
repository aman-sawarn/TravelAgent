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

    async def search_flights(self, flight_search_data_object: FetchedFlightSearchDetails) -> dict:
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
        Returns:."
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


if __name__ == "__main__":
    search = Search()
    flight_search_data = FetchedFlightSearchDetails(
        origin_iata="DEL",
        destination_iata="BLR",
        departure_date="2025-12-12",
        adults=1
    )
    try:
        print("Starting flight search...")
        results = asyncio.run(search.search_flights(flight_search_data))
        print(results)
        print("Search successful!")
    except Exception as e:
        print(f"Failed to search flights: {e}")
