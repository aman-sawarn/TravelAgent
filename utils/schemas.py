import sys
from typing import Optional
from pydantic import BaseModel, Field


class FetchIntent(BaseModel):
	"""Model to fetch intent for a given user"""
	intent: str = Field(..., description="", max_length=150)
	

class FlightSearchDetails(BaseModel):
	"""Model to fetch flight search details for standard/direct flight search"""
	origin_iata: str = Field(..., description="Origin city or Airport in the Journey", max_length=150)
	destination_iata: str = Field(..., description="Destination city or Airport in the Journey", max_length=150)
	departure_date: str = Field(..., description="Departure date in YYYY-MM-DD format", max_length=10)
	return_date: Optional[str] = Field(None, description="Return date in YYYY-MM-DD format", max_length=10)
	adults: Optional[int] = Field(1, description="Number of adult passengers", ge=1)
	children: Optional[int] = Field(0, description="Number of children passengers", ge=0)
	infants: Optional[int] = Field(0, description="Number of infant passengers", ge=0)
	currency: Optional[str] = Field("INR", description="Currency code for the flight search", max_length=3)
	travel_class: Optional[str] = Field("ECONOMY", description="Travel class for the flight search", max_length=20)
	non_stop: Optional[bool] = Field(False, description="Whether to search for non-stop flights only")
	max_results: Optional[int] = Field(10, description="Maximum number of flight options to return", ge=1)
	max_price: Optional[int] = Field(None, description="Maximum price for the flight search", ge=0.0)

class CheapestFlightSearchDetails(BaseModel):
	"""Model to fetch flight search details for finding cheapest flight dates"""
	origin_iata: str = Field(..., description="Origin city or Airport in the Journey", max_length=150)
	destination_iata: str = Field(..., description="Destination city or Airport in the Journey", max_length=150)
	departure_date: Optional[str] = Field(None, description="Departure date in YYYY-MM-DD format (Optional)", max_length=10)
	return_date: Optional[str] = Field(None, description="Return date in YYYY-MM-DD format", max_length=10)
	non_stop: Optional[bool] = Field(False, description="Whether to search for non-stop flights only")
	max_price: Optional[int] = Field(None, description="Maximum price for the flight search", ge=0.0)

	# def __str__(self) -> str:
	# 	return f"""{self.origin_iata} -> {self.destination_iata} on {self.departure_date}),
	# 	  Adults: {self.adults}, Children: {self.children}, Infants: {self.infants}, Currency: {self.currency},
	# 	  Class: {self.travel_class}, Non-stop: {self.non_stop}, Max Results: {self.max_results},
	# 	  Max Price: {self.max_price}, Return Date: {self.return_date}"""
