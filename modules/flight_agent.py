import asyncio, httpx
from typing import Optional
from ollama import chat
import json, os, sys
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.search import Search
from modules.schemas import FetchedFlightSearchDetails, FetchIntent


def fetch_intent_of_the_query(prompt: str, model_name: str = 'gemma3:4b') -> FetchIntent:
    """Extract the details from the prompt fetch the Intent of the user query"""

    extraction_prompt = f"""
    You are a helpful Travel Agent that the user intent from user prompts.

    Extract the Intent from the prompt using given details for each prompt:
    1. Find Flights: If the user is looking to search for flights between two cities on a given date, return find_flights.
    2. Find Cheapest Flight : If the user is looking to find the cheapest flight options available, return find_cheapest_flight.
    3. Find Direct Flights : If the user is looking to find non-stop flight options available, return find_direct_flights.
    
    Prompt: "{prompt}"

    Provide the details strictly in JSON format.
    """
    response = chat(
        model=model_name,  # or 'qwen3:8b' if available locally
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
        print(FetchIntent)
        raise ValueError(f"Parsed JSON does not match schema:\n{e}")

    return details


def fetch_flight_details(prompt: str, model_name: str = 'gemma3:4b') -> FetchedFlightSearchDetails:
    """Extract the details from the prompt required to search a Flight"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    extraction_prompt = f"""
    You are a helpful Travel Agent that extracts flight search details from user prompts.
    The Current date and time: {now}

    Extract the following details from the prompt:
    1. IATA code for Origin city
    2. IATA code for Destination city
    3. Departure date in YYYY-MM-DD format. If it is presented as relative date (like tomorrow, next Monday etc.), convert it to absolute date based on the current date and time:{now}.
    4. Return date in YYYY-MM-DD format (if mentioned)
    5. Maximum Results: Total number of flight options to return (if mentioned). If it is mentioned in words like 'five', convert it to numeric format.
    6. Sorting Preference: Whether to sort by price, duration, or departure time (if mentioned).
    7. Number of adult passengers (default is 1 if not mentioned) for whuch we need to search the flights. If it is mentioned in numbers like 'two adults', convert it to numeric format.
    8. Currency code for the flight search (default is INR if not mentioned)
    9. Travel class for the flight search (default is ECONOMY if not mentioned)
    10. Number of Infant passengers (default is 0 if not mentioned). If it is mentioned in numbers like 'one infant', 'an infant' convert it to numeric format.
    11. Number of Children passengers (default is 0 if not mentioned). If it is mentioned in numbers like 'two children', convert it to numeric format.
    12. Whether to search for non-stop flights only (default is False if not mentioned)
    13. Maximum price for the flight search (if mentioned). Eg: under 15k, below 20000 etc. Return value as a Int.

    Prompt: "{prompt}"

    Provide the details strictly in JSON format.
    """

    response = chat(
        model=model_name,  # or 'qwen3:8b' if available locally
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
        details = FetchedFlightSearchDetails(**parsed)
    except ValidationError as e:
        print(FetchedFlightSearchDetails)
        raise ValueError(f"Parsed JSON does not match schema:\n{e}")

    return details


if __name__ == "__main__":
    flight_details = fetch_flight_details(
        "Find me the flights for 2 adults and one infant between Delhi and Bengaluru tommorrow. show me top 5 results and flights under 15k")
    print("*-" * 40)
    print(flight_details)
    obj = Search()
    res = asyncio.run(obj.search_flights(flight_details))
    print(res)
    print(type(res))
    print(res['source'])
    print(res['results'].keys())
