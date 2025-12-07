import json
from datetime import datetime
from ollama import chat
from pydantic import ValidationError

from utils.schemas import FlightSearchDetails, CheapestFlightSearchDetails, FetchIntent
from config.main_config import model_name


def fetch_intent_of_the_query(prompt: str, model_to_be_used: str = model_name) -> FetchIntent:
	"""Extract the details from the prompt fetch the Intent of the user query"""

	extraction_prompt = f"""
    You are a helpful Travel Agent that the user intent from user prompts.

    Extract the Intent from the prompt using given details for each prompt:
    
    1. Find Cheapest Flight : If the user is looking to find the cheapest flight options available, return "find_cheapest_flight" in this case.
    2. Find Direct Flights : If the user is looking to find non-stop flight options available, return "find_direct_flights" in this case.
	3. Other: If the user is not looking to search for flights or hotels, return "other" in this case.

    Prompt: "{prompt}"

    Provide the details strictly in JSON format.
    """
	response = chat(
		model=model_to_be_used,  # or 'qwen3:8b' if available locally
		messages=[{'role': 'user', 'content': extraction_prompt}],
	)
	details_json = response['message']['content']
	# --- Clean and extract valid JSON ---
	try:
		# Remove markdown fences or extra text if the LLM adds them
		details_json = details_json.strip().strip("```").replace("json", "").strip()
		parsed = json.loads(details_json)
	except json.JSONDecodeError as e:
		raise ValueError(f"LLM returned invalid JSON:\n{details_json}\nError: {e}")
	# --- Validate and format using the Pydantic model ---
	try:
		details = FetchIntent(**parsed)
	except ValidationError as e:
		raise ValueError(f"Parsed JSON does not match schema:\n{e}")

	return details


def fetch_standard_flight_details(user_prompt: str, current_model: str = model_name) -> FlightSearchDetails:
	"""Extract the details from the prompt required to search a Flight (Standard/Direct)"""
	now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	extraction_prompt = f"""
	You are a helpful Travel Agent that extracts flight search details from user prompts.
	The Current date and time: {now}

	Extract the following details from the prompt:
	1. "origin_iata": IATA code for Origin city
	2. "destination_iata": IATA code for Destination city
	3. "departure_date": Departure date in YYYY-MM-DD format. If it is presented as relative date (like tomorrow, next Monday etc.), convert it to absolute date based on the current date and time:{now}.
	4. "return_date": Return date in YYYY-MM-DD format (if mentioned)
	5. "max_results": Total number of flight options to return (if mentioned). If it is mentioned in words like 'five', convert it to numeric format.
	6. Sorting Preference: Whether to sort by price, duration, or departure time (if mentioned).
	7. "adults": Number of adult passengers (default is 1 if not mentioned) for whuch we need to search the flights. If it is mentioned in numbers like 'two adults', convert it to numeric format.
	8. "currency": Currency code for the flight search (default is INR if not mentioned)
	9. "travel_class": Travel class for the flight search (default is ECONOMY if not mentioned)
	10. "infants": Number of Infant passengers (default is 0 if not mentioned). If it is mentioned in numbers like 'one infant', 'an infant' convert it to numeric format.
	11. "children": Number of Children passengers (default is 0 if not mentioned). If it is mentioned in numbers like 'two children', convert it to numeric format.
	12. "non_stop": Whether to search for non-stop flights only (default is False if not mentioned) - usually False unless direct is requested.
	13. "max_price": Maximum price for the flight search (if mentioned). Eg: under 15k, below 20000 etc. Return value as a Int.

	Prompt: "{user_prompt}"

	Provide the details strictly in JSON format.
	"""

	response = chat(model=current_model, messages=[{'role': 'user', 'content': extraction_prompt}])
	details_json = response['message']['content']

	try:
		details_json = details_json.strip().strip("```").replace("json", "").strip()
		parsed = json.loads(details_json)
	except json.JSONDecodeError as e:
		raise ValueError(f"LLM returned invalid JSON:\n{details_json}\nError: {e}")
	try:
		details = FlightSearchDetails(**parsed)
	except ValidationError as e:
		print(FlightSearchDetails)
		raise ValueError(f"Parsed JSON does not match schema:\n{e}")

	return details


def fetch_cheapest_flight_details(user_prompt: str, current_model: str = model_name) -> CheapestFlightSearchDetails:
	"""Extract the details from the prompt required to search for Cheapest Flight Dates"""
	now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	extraction_prompt = f"""
	You are a helpful Travel Agent that extracts details for finding the CHEAPEST FLIGHT DATES.
	The Current date and time: {now}

	Extract the following details from the prompt:
	1. "origin_iata": IATA code for Origin city
	2. "destination_iata": IATA code for Destination city
	3. "departure_date": Departure date in YYYY-MM-DD format (Optional).
	4. "return_date": Return date in YYYY-MM-DD format (if mentioned)
	5. "non_stop": Whether to search for non-stop flights only (default is False)
	6. "max_price": Maximum price for the flight search (if mentioned). Return value as a Int.

	Prompt: "{user_prompt}"

	Provide the details strictly in JSON format.
	"""

	response = chat(model=current_model, messages=[{'role': 'user', 'content': extraction_prompt}])
	details_json = response['message']['content']

	try:
		details_json = details_json.strip().strip("```").replace("json", "").strip()
		parsed = json.loads(details_json)
	except json.JSONDecodeError as e:
		raise ValueError(f"LLM returned invalid JSON:\n{details_json}\nError: {e}")
	try:
		details = CheapestFlightSearchDetails(**parsed)
	except ValidationError as e:
		print(CheapestFlightSearchDetails)
		raise ValueError(f"Parsed JSON does not match schema:\n{e}")

	return details
