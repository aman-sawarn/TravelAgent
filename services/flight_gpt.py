import asyncio
import os
import sys
import pandas as pd
# Add project root to sys.path (parent of services/)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.sensors import UserIntent

from utils.prompts import fetch_standard_flight_details, fetch_intent_of_the_query
from services.environment import Search
from config.main_config import model_name
from utils.output_reader import flight_offer_list_reader


def flight_search_result_sorted(responses: list) -> list:
	"""sort the results based on price"""
	responses = list(sorted(responses, key=lambda x: x['price']['total'], reverse=False))
	return responses


if __name__ == "__main__":
	prompt = "Find me cheapest flights between Madrid and London tommorrow."
	user_intent = fetch_intent_of_the_query(prompt) 
	print("*-" * 40)
	print("intent : ", user_intent)
	
	obj = Search()
	
	if user_intent.intent == UserIntent.FIND_FLIGHTS_ADVANCED:
		print(f"{user_intent.intent} detected, using advanced search")
		
		# Check if the user is looking for a date range/cheapest dates
		# fetch_intent_of_the_query now returns date_range boolean
		if user_intent.date_range:
			print("Date Range / Flexible Dates detected.")
			from utils.prompts import fetch_cheapest_flight_details
			flight_details = fetch_cheapest_flight_details(prompt)
		else:
			print("Specific Date detected.")
			flight_details = fetch_standard_flight_details(prompt)
			
		print("flight_details : ", flight_details) 
		res = asyncio.run(obj.search_flights_advanced(flight_details)) 
		if 'data' in res.get('results', {}):
			ans = flight_offer_list_reader(res['results']['data'])
			print(ans)
		else:
			print("No flight data found or Mock Error:", res.get("error"))
		
	elif user_intent.intent == UserIntent.FIND_FLIGHTS_STANDARD: 
		print(f"{user_intent.intent} detected, using standard search") 
		flight_details = fetch_standard_flight_details(prompt)
		print("flight_details : ", flight_details)
		res = asyncio.run(obj.search_flights_on_a_date(flight_details))
		if 'data' in res.get('results', {}):
			ans = flight_offer_list_reader(res['results']['data'])
			print(ans)
		else:
			print("No flight data found.")
	else:
		print(f"Unknown intent: {user_intent.intent} or 'other'")


	print("*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-")

