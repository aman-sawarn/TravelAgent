import json
from datetime import datetime
from ollama import chat
from pydantic import ValidationError

from utils.schemas import FlightSearchQueryDetails, CheapestFlightSearchDetails, FetchIntent
from config.main_config import model_name


def fetch_intent_of_the_query(prompt: str, model_to_be_used: str = model_name) -> FetchIntent:
	"""Extract the details from the prompt fetch the Intent of the user query"""

	extraction_prompt = f"""
    You are a helpful Travel Agent that identifies the user intent from user prompts.

    Extract the Intent from the prompt:
    
    1. "find_flights_advanced": If the user is looking for flight options with specific sorting (e.g. cheapest, fastest, earliest) OR advanced filtering (e.g. max stops, refundable, specific airlines, seat count) OR searching for cheapest dates. 
       - KEYWORDS: "cheapest", "fastest", "shortest duration", "direct", "min seats", "refundable", "sort by".
    
    2. "find_flights_standard": If the user is making a simple point-to-point flight search without complex sorting or advanced filters (other than basic class/passengers).
       - KEYWORDS: "find flights", "show me flights", "flights from X to Y".
    
    3. "other": If the user is not looking to search for flights, return "other".

    Prompt: "{prompt}"

    Provide the details strictly in JSON format with key "intent".
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
		# For robustness, let's default to standard if parsing fails but logged
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


def fetch_cheapest_flight_details(user_prompt: str, current_model: str = model_name) -> CheapestFlightSearchDetails:
	"""Extract details for Cheapest Date Search (Flexible Dates)"""
	now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	extraction_prompt = f"""
    You are a helpful Travel Agent extracting details for finding CHEAPEST FLIGHT DATES/RANGES.
	Current time: {now}

	Extract:
	1. "origin": IATA code.
	2. "destination": IATA code (Optional).
	3. "departure_date": YYYY-MM-DD or comma-separated range (Optional).
	4. "return_date": YYYY-MM-DD or range (Optional).
	5. "nonStop": Boolean.
	6. "maxPrice": Int (Optional).
	7. "oneWay": Boolean (Default True unless return date specified).

	Prompt: "{user_prompt}"

    Provide details strictly in JSON.
	"""

	response = chat(model=current_model, messages=[{'role': 'user', 'content': extraction_prompt}])
	details_json = response['message']['content']

	try:
		details_json = details_json.strip().strip("```").replace("json", "").strip()
		parsed = json.loads(details_json)
		details = CheapestFlightSearchDetails(**parsed)
	except (json.JSONDecodeError, ValidationError) as e:
		raise ValueError(f"LLM Error:\n{details_json}\n{e}")

	return details
