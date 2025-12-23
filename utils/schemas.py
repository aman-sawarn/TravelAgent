import sys
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field

class UserIntent(str, Enum):
	FIND_FLIGHTS_ADVANCED = "find_flights_advanced"
	FIND_FLIGHTS_STANDARD = "find_flights_standard"
	OTHER = "other"

class FetchIntent(BaseModel):
	"""Model to fetch intent for a given user"""
	intent: UserIntent = Field(..., description="User's intent string")
	date_range: Optional[bool] = Field(False, description="User's Date Range")


class SortBy(str, Enum):
	PRICE = "price"
	DURATION = "duration"
	DEPARTURE_TIME = "generated_departure_time"
	ARRIVAL_TIME = "generated_arrival_time"
	SEATS = "number_of_bookable_seats"
	LAST_TICKETING_DATE = "last_ticketing_date"

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
	min_bookable_seats: Optional[int] = Field(None, description="Minimum number of bookable seats required")
	instant_ticketing_required: Optional[bool] = Field(False, description="Whether to filter for flights that require instant ticketing")
