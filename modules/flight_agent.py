import asyncio, httpx
from typing import Optional
from ollama import chat
import json, os, sys
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.search import Search
from modules.schemas import FetchFlightSearchDetails
import pandas as pd


def fetch_flight_details(prompt: str) -> FetchFlightSearchDetails:
    """Extract the details from the prompt required to search a Flight"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    extraction_prompt = f"""
    You are a helpful assistant that extracts flight search details from user prompts.
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
        model='gemma3:4b',  # or 'qwen3:8b' if available locally
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
        details = FetchFlightSearchDetails(**parsed)
    except ValidationError as e:
        print(FetchFlightSearchDetails)
        raise ValueError(f"Parsed JSON does not match schema:\n{e}")

    return details


def format_search_results(flight_result_dict) -> str:
    """Given the python dict, rewrite it in a Tabular format and present the output in a markdown table."""

    extraction_prompt = f"""Given the python dict, Convert it into a different format (e.g., a table): {flight_result_dict}"""

    response = chat(
        model='gemma3:4b',  # or 'qwen3:8b' if available locally
        messages=[{'role': 'user', 'content': extraction_prompt}],
    )
    details_json = response['message']['content']
    return details_json


async def find_flights(search_details: FetchFlightSearchDetails):
    """Use the extracted flight details to search for flights using the Search module."""
    search = Search()
    # results= asyncio.run(search.search_flights(origin=search_details.origin_iata,
    #                                       destination=search_details.destination_iata,
    #                                       departDate=search_details.departure_date, returnDate=search_details.return_date,
    #                                       adults=search_details.adults,
    #                                       nonStop=search_details.non_stop,
    #                                       currency=search_details.currency,
    #                                       travel_class=search_details.travel_class,
    #                                       children=search_details.children,
    #                                       infants=search_details.infants,
    #                                       max_results=search_details.max_results))

    try:
        search = Search()
        results = await search.search_flights(
            origin=search_details.origin_iata,
            destination=search_details.destination_iata,
            departDate=search_details.departure_date,
            returnDate=search_details.return_date,
            adults=search_details.adults,
            children=search_details.children,
            infants=search_details.infants,
            max_price=int(search_details.max_price),
            travel_class=search_details.travel_class,
            non_stop=search_details.non_stop,
            currency=search_details.currency,
            max_results=search_details.max_results,
        )
        return results
    except httpx.RequestError as e:
        print(f"An error occurred while making the HTTP request: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise

    return results


if __name__ == "__main__":
    flight_details = fetch_flight_details(
        "Find me the flights for 2 adults and one infant between Delhi and Bengaluru tommorrow. show me top 5 results and flights under 15k")
    print(flight_details)
    obj = Search()
    res = asyncio.run(obj.search_flights(flight_details))
    print(res)
    print(type(res))
    print(res['source'])
    print(res['results'].keys())
    # print(format_search_results(str(res)))
    # df = pd.DataFrame(res['results']['data'])
    # print(find_flights(flight_details))
    # print(df.head())
    # df.to_csv("flight_search_results.csv", index=False)
