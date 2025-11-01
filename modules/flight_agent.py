import asyncio
import os
import sys
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.prompts import fetch_flight_details, fetch_intent_of_the_query
from modules.search import Search
from config.main_config import model_name
from utils.output_reader import flight_offer_list_reader


def flight_search_result_sorted(responses: list) -> list:
	"""sort the results based on price"""
	responses = list(sorted(responses, key=lambda x: x['price']['total'], reverse=False))
	return responses


def show_results_in_dataframe(responses: list) -> pd.DataFrame:
	"""Show the flight search results in a pandas DataFrame"""
	df = pd.DataFrame(responses)
	return df


if __name__ == "__main__":
	prompt = "Find me the cheapest flights for 2 adults and one infant between Delhi and Bengaluru tommorrow. Show me top 5 results and flights under 15k"
	user_intent = fetch_intent_of_the_query(prompt)
	print("*-" * 40)
	flight_details = fetch_flight_details(prompt)
	obj = Search()
	res = asyncio.run(obj.search_flights(flight_details))
	if user_intent == "find_cheapest_flight":
		sorted_responses = flight_search_result_sorted(res['results']['data'])
		res['results']['data'] = sorted_responses

	print(flight_offer_list_reader(res))
