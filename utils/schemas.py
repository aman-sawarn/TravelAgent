import sys
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class FetchIntent(BaseModel):
	"""Model to fetch intent for a given user"""
	intent: str = Field(..., description="", max_length=150)
	

class SortBy(str, Enum):
	PRICE = "price"
	DURATION = "duration"
	DEPARTURE_TIME = "generated_departure_time" # Note: Amadeus might name this differently or we sort client side
	ARRIVAL_TIME = "generated_arrival_time"

class FlightSearchQueryDetails(BaseModel):
	"""Model to fetch flight search details for standard/direct flight search"""
	origin_iata: str = Field(..., description="Origin city or Airport in the Journey", max_length=150)
	destination_iata: str = Field(..., description="Destination city or Airport in the Journey", max_length=150)
	departure_date: Optional[str] = Field(None, description="Departure date in YYYY-MM-DD format", max_length=10)
	return_date: Optional[str] = Field(None, description="Return date in YYYY-MM-DD format", max_length=10)
	adults: Optional[int] = Field(1, description="Number of adult passengers", ge=1)
	children: Optional[int] = Field(0, description="Number of children passengers", ge=0)
	infants: Optional[int] = Field(0, description="Number of infant passengers", ge=0)
	currency: Optional[str] = Field("INR", description="Currency code for the flight search", max_length=3)
	travel_class: Optional[str] = Field("ECONOMY", description="Travel class for the flight search", max_length=20)
	non_stop: Optional[bool] = Field(False, description="Whether to search for non-stop flights only")
	max_results: Optional[int] = Field(10, description="Maximum number of flight options to return", ge=1)
	max_price: Optional[int] = Field(None, description="Maximum price for the flight search", ge=0.0)
	sort_by: Optional[SortBy] = Field(SortBy.PRICE, description="Criteria to sort the results by")
	max_stops: Optional[int] = Field(None, description="Maximum number of stops (0, 1, 2). If 0, same as non_stop=True", ge=0, le=2)
	included_airlines: Optional[List[str]] = Field(None, description="List of IATA codes of airlines to include")
	excluded_airlines: Optional[List[str]] = Field(None, description="List of IATA codes of airlines to exclude")

class CheapestFlightSearchDetails(BaseModel):
	"""Model to fetch flight search details for finding the cheapest flight dates"""
	origin: str = Field(..., description="Origin city or Airport in the Journey", max_length=150)
	destination: str = Field(..., description="Destination city or Airport in the Journey. If not provided, searches for cheapest destinations anywhere.", max_length=150)
	departure_date: Optional[str] = Field(None, description="the date, or range of dates, on which the flight will depart from the origin. Dates are specified in the ISO 8601 YYYY-MM-DD format, e.g. 2017-12-25. Ranges are specified with a comma and are inclusive", max_length=21)
	return_date: Optional[str] = Field(None, description="the date, or range of dates, on which the flight will depart from the origin. Dates are specified in the ISO 8601 YYYY-MM-DD format, e.g. 2017-12-25. Ranges are specified with a comma and are inclusive", max_length=21)
	nonStop: Optional[bool] = Field(False, description="Whether to search for non-stop flights only")
	maxPrice: Optional[int] = Field(None, description="Maximum price for the flight search", ge=0.0)
	oneWay: Optional[bool] = Field(True, description="Whether to search for one-way flights only")
	