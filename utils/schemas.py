import sys
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field

class UserIntent(str, Enum):
	FIND_FLIGHTS_ADVANCED = "find_flights_advanced"
	FIND_FLIGHTS_STANDARD = "find_flights_standard"
	OTHER = "other"

class DateRangeDetails(BaseModel):
    """Model to extract date range details from user prompt"""
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
    end_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format")
    is_range: bool = Field(False, description="Whether the user specified a date range")


class SortBy(str, Enum):
	PRICE = "price"
	DURATION = "duration"
	DEPARTURE_TIME = "generated_departure_time"
	ARRIVAL_TIME = "generated_arrival_time"
	SEATS = "number_of_bookable_seats"
	LAST_TICKETING_DATE = "last_ticketing_date"

class FetchIntent(BaseModel):
	"""Model to fetch intent for a given user"""
	intent: UserIntent = Field(..., description="User's intent string")
	date_range: Optional[bool] = Field(None, description="True if user has given a date range eg. next week, next month, this weekend, this month, this year, etc. False otherwise")
	date_range_details: Optional[DateRangeDetails] = Field(None, description="Date range details if date_range is True")
	multicity_trip: Optional[bool] = Field(None, description="True if user has given a multicity trip eg. from X to Y to Z and back to X. eg. X, Y and Z coming back to X, False otherwise")
	sorting_details: Optional[SortBy] = Field(None, description="Sorting details if user has given a sorting preference")
	def __str__(self):
		return f"intent={self.intent} date_range={self.date_range} date_range_details={self.date_range_details} multicity_trip={self.multicity_trip} sorting_details={self.sorting_details}"


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

class HotelSearchQueryDetails(BaseModel):
    """Model to fetch hotel search details for hotel search"""
    city_code: str = Field(..., description="City code for the hotel search", max_length=150)
    radius: Optional[int] = Field(5, description="Radius in kilometers for the hotel search", ge=1)
    radius_unit: Optional[str] = Field("KM", description="Radius unit for the hotel search", max_length=2)
    ratings: Optional[List[int]] = Field(None, description="List of ratings for the hotel search")
    amenities: Optional[List[str]] = Field(None, description="List of amenities to filter hotels. Available values: SWIMMING_POOL, SPA, FITNESS_CENTER, AIR_CONDITIONING, RESTAURANT, PARKING, PETS_ALLOWED, AIRPORT_SHUTTLE, BUSINESS_CENTER, DISABLED_FACILITIES, WIFI, MEETING_ROOMS, NO_KID_ALLOWED, TENNIS, GOLF, KITCHEN, ANIMAL_WATCHING, BABY-SITTING, BEACH, CASINO, JACUZZI, SAUNA, SOLARIUM, MASSAGE, VALET_PARKING, BAR or LOUNGE, KIDS_WELCOME, NO_PORN_FILMS, MINIBAR, TELEVISION, WI-FI_IN_ROOM, ROOM_SERVICE, GUARDED_PARKG, SERV_SPEC_MENU")
    max_results: Optional[int] = Field(10, description="Maximum number of hotel options to return", ge=1)
    min_stars: Optional[int] = Field(None, description="Minimum number of stars for the hotel search", ge=1, le=5)
    max_price: Optional[int] = Field(None, description="Maximum price for the hotel search", ge=0.0)
    