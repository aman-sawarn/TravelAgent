import os
import sys


def read_flight_offer_(data):
	"""
	Extracts and formats specific information from a flight offer dictionary.
	Args:
		data: A dictionary representing a flight offer.
	Returns:
		A dictionary containing selected key information from the flight offer.
	"""

	readable_output = {}
	itineraries = data.get('itineraries', [])
	if itineraries:
		readable_output['Flight Number'] = itineraries[0].get('segments', [])[0].get('number', 'N/A')
		readable_output['Departure'] = itineraries[0].get('segments', [])[0].get('departure', {}).get('iataCode', 'N/A')
		readable_output['Departure Time'] = itineraries[0].get('segments', [])[0].get('departure', {}).get('at', 'N/A')
		readable_output['Arrival'] = itineraries[0].get('segments', [])[-1].get('arrival', {}).get('iataCode', 'N/A')
		readable_output['Arrival Time'] = itineraries[0].get('segments', [])[-1].get('arrival', {}).get('at', 'N/A')
		readable_output['Duration'] = itineraries[0].get('duration', 'N/A')
		"""Assuming the total number of stops is the sum of stops in each segment"""
		total_stops = sum(segment.get('numberOfStops', 0) for segment in itineraries[0].get('segments', []))
		readable_output['Number of Stops'] = total_stops

	price_info = data.get('price', {})
	if price_info:
		grand_total = price_info.get('grandTotal', 'N/A')
		currency = price_info.get('currency', 'N/A')
		readable_output['Price'] = f"{grand_total} {currency}"

	return readable_output


def flight_offer_list_reader(offers: list) -> list:
	"""Read a list of flight offers and return a list of readable flight details."""
	# offers = offers['results']['data']
	print(len(offers))
	readable_offers = []
	for offer in offers:
		readable_offer = read_flight_offer_(offer)
		readable_offers.append(readable_offer)
	return readable_offers
