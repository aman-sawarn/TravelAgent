from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os
import asyncio

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.sensors import UserIntent
from utils.prompts import fetch_standard_flight_details, fetch_intent_of_the_query, fetch_date_range_from_query, fetch_hotel_details
from services.environment import Actuator
from utils.output_reader import flight_offer_list_reader

app = FastAPI(title="Travel Agent API")

class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    response: str
    data: list = []
    intent: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    prompt = request.prompt
    
    try:
        # 1. Determine Intent
        user_intent = fetch_intent_of_the_query(prompt)
        intent_str = user_intent.intent.value
        
        actuator = Actuator()
        
        if user_intent.intent == UserIntent.FIND_FLIGHTS_ADVANCED:
             # Check for date range
            if user_intent.date_range:
                flight_details = fetch_cheapest_flight_details(prompt)
                search_method = actuator.search_flights_advanced
            else:
                flight_details = fetch_standard_flight_details(prompt)
                search_method = actuator.search_flights_advanced

            # Execute Search
            res = await search_method(flight_details)
            
            if 'data' in res.get('results', {}):
                offers = flight_offer_list_reader(res['results']['data'])
                return ChatResponse(
                    response=f"Found {len(offers)} flights for your request.",
                    data=offers,
                    intent=intent_str
                )
            else:
                return ChatResponse(
                    response="I couldn't find any flights matching your criteria.",
                    data=[],
                    intent=intent_str
                )

        elif user_intent.intent == UserIntent.FIND_FLIGHTS_STANDARD:
            flight_details = fetch_standard_flight_details(prompt)
            res = await actuator.search_flights_on_a_date(flight_details)
            
            if 'data' in res.get('results', {}):
                 offers = flight_offer_list_reader(res['results']['data'])
                 return ChatResponse(
                    response=f"Found {len(offers)} flights for your request.",
                    data=offers,
                    intent=intent_str
                )
            else:
                 return ChatResponse(
                    response="I couldn't find any flights matching your criteria.",
                    data=[],
                    intent=intent_str
                )
        
        else:
            # Fallback for "OTHER" or unhandled intents
            return ChatResponse(
                response="I am a specialized Travel Agent. Currently, I can help you find flights. Try asking: 'Find me cheapest flights from Delhi to Mumbai tomorrow'.",
                data=[],
                intent=intent_str
            )

    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
