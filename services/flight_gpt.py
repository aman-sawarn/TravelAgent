import asyncio
import os
import sys
import pandas as pd
# Add project root to sys.path (parent of services/)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.prompts import fetch_standard_flight_details, fetch_cheapest_flight_details, fetch_intent_of_the_query
from services.flight_search import Search
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
	
	if user_intent.intent == "find_flights_advanced":
		print(f"{user_intent.intent} detected, using advanced search")
        # Use simple standard details extraction which now supports advanced fields?
        # Note: If intent is "cheapest flight dates" specifically, we might need fetch_cheapest_flight_details.
        # But prompts.py now has unified intent for "advanced" covering filtering.
        # Let's try flight_details standard first as it covers almost everything except flexible date ranges?
        # Actually, for "find_cheapest_flight_dates", we might want separate handling if we kept that function.
        # But the prompt says "find_flights_advanced" covers "searching for cheapest dates".
        # Let's check prompt context. If "cheapest dates" we need CheapesSchema.
        # However, for now, let's map advanced to Standard Details + Advanced Search 
        # OR CheapesDetails if prompt implies date range?
        # For simplicity, use Standard Details as it has sort/filter.
		flight_details = fetch_standard_flight_details(prompt) 
		print("flight_details : ", flight_details) 
		res = asyncio.run(obj.search_flights_advanced(flight_details)) 
		if 'data' in res.get('results', {}):
			ans = flight_offer_list_reader(res['results']['data'])
			print(ans)
		else:
			print("No flight data found or Mock Error:", res.get("error"))
		
	elif user_intent.intent == "find_flights_standard": 
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

