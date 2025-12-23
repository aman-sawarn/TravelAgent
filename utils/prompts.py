import json
from datetime import datetime
from ollama import chat
from pydantic import ValidationError
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.schemas import FlightSearchQueryDetails, FetchIntent, DateRangeDetails
from config.main_config import model_name

def fetch_date_range_from_query(prompt: str, model_to_be_used: str = model_name) -> DateRangeDetails:
	"""
    Extract specific date or date range details from the user query.
    
    This function uses an LLM to identify and extract date information from a natural language prompt.
    It handles both single dates and date ranges, converting relative terms (e.g., "next week") 
    into absolute ISO 8601 (YYYY-MM-DD) format.
    
    Args:
        prompt (str): The user's natural language query.
        model_to_be_used (str): The LLM model identifier to use (default from config).
        
    Returns:
        DateRangeDetails: A Pydantic object containing:
            - start_date (Optional[str]): The starting date of the range or the single date found.
            - end_date (Optional[str]): The ending date of the range (if applicable).
            - is_range (bool): True if a range was detected, False otherwise.
    """
	now = datetime.now().strftime("%Y-%m-%d")
	extraction_prompt = f"""
    Current date: {now}
    Extract the date or date range mentioned in the user prompt. 
    Convert relative terms (e.g., "next Monday", "this weekend", "in two weeks") into absolute YYYY-MM-DD format.

    Prompt: "{prompt}"

    Return JSON format only:
    {{
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD",
        "is_range": boolean
    }}
    """
	response = chat(
		model=model_to_be_used,
		messages=[{'role': 'user', 'content': extraction_prompt}],
	)
	try:
		details_json = response['message']['content'].strip().strip("```").replace("json", "").strip()
		parsed = json.loads(details_json)
		return DateRangeDetails(**parsed)
	except (json.JSONDecodeError, Exception):
		return DateRangeDetails(start_date=None, end_date=None, is_range=False)


def fetch_intent_of_the_query(prompt: str, model_to_be_used: str = model_name) -> FetchIntent:
	"""Extract the details from the prompt fetch the Intent of the user query"""
	now = datetime.now().strftime("%Y-%m-%d")

	extraction_prompt = f"""
    You are a helpful Travel Agent that identifies the user intent from user prompts.
    Current date: {now}

    Extract the Intent from the prompt:
    
    1. "find_flights_advanced": If the user is looking for flight options with specific sorting (e.g. cheapest, fastest, earliest) OR advanced filtering (e.g. max stops, refundable, specific airlines, seat count) OR searching for cheapest dates. 
       - KEYWORDS: "cheapest", "fastest", "shortest duration", "direct", "min seats", "refundable", "sort by".
    
    2. "find_flights_standard": If the user is making a simple point-to-point flight search without complex sorting or advanced filters (other than basic class/passengers).
       - KEYWORDS: "find flights", "show me flights", "flights from X to Y".
    
    3. "other": If the user is not looking to search for flights, return "other".

    Prompt: "{prompt}"

    Provide the details strictly in JSON format with keys matching the Pydantic schema:
    - "intent": One of "find_flights_advanced", "find_flights_standard", "other".
    - "date_range": Boolean. True if the user implies flexible dates, a date range (e.g. "next week", "in December").
    - "date_range_details": Object with "start_date" (YYYY-MM-DD), "end_date" (YYYY-MM-DD), "is_range" (bool). Only populate if date_range is True.
    - "multicity_trip": Boolean. True if user has given a multicity trip (e.g. X->Y->Z->X).
    - "sorting_details": String. One of "price", "duration", "generated_departure_time", "generated_arrival_time", "number_of_bookable_seats", "last_ticketing_date". Only populate if user has given a sorting preference.
    """
	response = chat(
		model=model_to_be_used,
		messages=[{'role': 'user', 'content': extraction_prompt}],
	)
	details_json = response['message']['content']
	try:
		details_json = details_json.strip().strip("```").replace("json", "").strip()
		parsed = json.loads(details_json)
		details = FetchIntent(**parsed)
	except (json.JSONDecodeError, ValidationError) as e:
		# Fallback to standard if ambiguous or error, or raise
		print(f"Intent Parsing Error: {e}")
		details = FetchIntent(intent="find_flights_standard")

	return details


def fetch_standard_flight_details(user_prompt: str, current_model: str = model_name) -> FlightSearchQueryDetails:
	"""Extract details for Standard/Advanced Flight Search (Unified in FlightSearchQueryDetails)"""
	now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	extraction_prompt = f"""
	You are a helpful Travel Agent that extracts flight search details.
	Current time: {now}

	Extract the following FlightSearchQueryDetails from the prompt:
	1. "origin_iata": IATA code (e.g. LON, JFK).
	2. "destination_iata": IATA code.
	3. "departure_date": YYYY-MM-DD. Convert relative dates (tomorrow, next Fri) to absolute.
	4. "return_date": YYYY-MM-DD (Optional).
	5. "adults": Int (Default 1).
	6. "children": Int (Default 0).
	7. "infants": Int (Default 0).
	8. "travel_class": "ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST" (Default ECONOMY).
	9. "currency": Default "INR".
	10. "non_stop": Boolean (True/False).
	11. "max_price": Int (Optional).
	12. "max_results": Int (Default 10).
	13. "sort_by": Options: "price", "duration", "generated_departure_time", "generated_arrival_time", "number_of_bookable_seats", "last_ticketing_date". 
        - Default to "price" if "cheapest" is asked.
        - Default to "duration" if "fastest/shortest" is asked.
    14. "max_stops": Int (0, 1, 2). If "direct" or "non-stop" is requested, set max_stops=0.
    15. "min_bookable_seats": Int (Optional).
    16. "instant_ticketing_required": Boolean (Optional).

	Prompt: "{user_prompt}"

	Provide details strictly in JSON.
	"""

	response = chat(model=current_model, messages=[{'role': 'user', 'content': extraction_prompt}])
	details_json = response['message']['content']

	try:
		details_json = details_json.strip().strip("```").replace("json", "").strip()
		parsed = json.loads(details_json)
		details = FlightSearchQueryDetails(**parsed)
	except (json.JSONDecodeError, ValidationError) as e:
		raise ValueError(f"LLM Error:\n{details_json}\n{e}")
	return details

if __name__ == "__main__":
	# Example usage
	user_prompt = "plan a trip from BLR to BOM next month"
	
	print(f"Prompt: {user_prompt}\n")

	# 1. Fetch Intent
	intent_result = fetch_intent_of_the_query(user_prompt)
	print(f"Intent Result:\n{intent_result}\n")

	# # 2. Fetch Date Range
	# date_range_result = fetch_date_range_from_query(user_prompt)
	# print(f"Date Range Result:\n{date_range_result}")