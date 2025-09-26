def flight_search_mock(origin, dest, dep, ret=None):
    return [
    {"offerId": "MOCK-F1", "price": {"amount": 45000, "currency": "INR"}, "itinerary": [{"from": origin, "to": dest, "depart": dep, "duration": "6h 10m"}], "airline": "AI", "stops": 0},
    {"offerId": "MOCK-F2", "price": {"amount": 38000, "currency": "INR"}, "itinerary": [{"from": origin, "to": dest, "depart": dep, "duration": "9h 40m", "stops": 1}], "airline": "EK", "stops": 1}
    ]


def flight_booking_mock(offerId, traveler):
    return {"pnr": f"MOCKPNR-{offerId}", "status": "CONFIRMED", "traveler": traveler}


def hotel_search_mock(dest, ci, co):
    return [
    {"hotelId": "MK-H1", "name": "Demo Grand", "pricePerNight": 7000, "currency": "INR", "rating": 4.4},
    {"hotelId": "MK-H2", "name": "City Comfort", "pricePerNight": 4500, "currency": "INR", "rating": 4.0}
    ]


def hotel_booking_mock(hotelId, roomId, guest):
    return {"confirmation": f"HOTEL-{int(time.time())}", "hotelId": hotelId, "guest": guest}