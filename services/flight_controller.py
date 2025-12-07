import asyncio
import os
import sys
import pandas as pd

from app.core.prompts import fetch_flight_details, fetch_intent_of_the_query
from app.services.flight_service import Search
from app.config.main_config import model_name
from app.utils.output_reader import flight_offer_list_reader


def flight_search_result_sorted(responses: list) -> list:
	"""sort the results based on price"""
	responses = list(sorted(responses, key=lambda x: x['price']['total'], reverse=False))
	return responses


if __name__ == "__main__":
	prompt = "Find me the flights for 2 adults and one infant between Delhi and Bengaluru tommorrow. Show me top 5 results and flights under 15k"
	user_intent = fetch_intent_of_the_query(prompt) 
	print("*-" * 40)
	print("intent : ", user_intent)
	flight_details = fetch_flight_details(prompt)
	print("flight_details : ", flight_details)
	# obj = Search()
	# res = asyncio.run(obj.search_flights(flight_details))
	# print(res.keys())
	# print(user_intent.intent)
	# if user_intent.intent == "find_cheapest_flight":
	# 	print(f"{user_intent.intent} detected, using tool find_cheapest_flights")
	# 	ans = flight_offer_list_reader(res['results']['data'])
	# 	sorted_responses = flight_offer_list_reader(ans) 
	# 	print(sorted_responses)
	# elif user_intent == "find_flights":
	# 	print(f"{user_intent.intent} detected, using tool find_flights")
	# 	ans = flight_offer_list_reader(res['results']['data'])
	# 	print(ans)
	# else:
	# 	pass


	print("*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-")

