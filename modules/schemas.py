import asyncio, httpx
from typing import Optional
from ollama import chat
import json, os, sys
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FetchFlightSearchDetails(BaseModel):
    """Model to fetch flight search details from a given prompt"""
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
    max_price: Optional[float] = Field(None, description="Maximum price for the flight search", ge=0.0)
