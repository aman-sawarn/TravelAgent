import os
import sys
from typing import Optional

from ollama import chat

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def add(a,b):
  """Adds two numbers

  Args:
    a: Number 1
    b: Number 2
    Returns:
    The sum of the two numbers
    """
  return a+b

def get_temperature(city: str) -> str:
  """Get the current temperature for a city
  
  Args:
    city: The name of the city

  Returns:
    The current temperature for the city
  """
  temperatures = {
    'New York': '22°C',
    'London': '15°C',
  }
  return temperatures.get(city, 'Unknown')

# @tool
def flight_search(origin: str, dest: str, depart_date: str, return_date: Optional[str] = None, passengers: int = 1):
    """Mock flight search tool. Replace with real flights API (Amadeus, Skyscanner, etc.)."""
    # In a real implementation call an external API and return structured results.
    return [
    {"carrier": "ExampleAir", "price": "₹12,345", "depart": depart_date, "origin": origin, "dest": dest, "flight_no": "EA123"},
    {"carrier": "DemoJet", "price": "₹15,200", "depart": depart_date, "origin": origin, "dest": dest, "flight_no": "DJ456"},
    ]


# @tool
def hotel_search(city: str, checkin: str, checkout: str, guests: int = 1):
    """Mock hotel search tool. Replace with calls to Booking/Hotels API."""
    return [
    {"hotel": "The Sample Residency", "price_per_night": "₹4,500", "rating": 4.3},
    {"hotel": "Demo Inn", "price_per_night": "₹3,200", "rating": 3.9},
    ]

messages = [{'role': 'user', 'content': "Find me flights between Delhi and Banglore tommorow. The date today is october 16, 2025"}]

while True:
  stream = chat(
    model='qwen3:8b',
    messages=messages,
    tools=[ flight_search, hotel_search],
    stream=True,
    think=True,
  )

  thinking = ''
  content = ''
  tool_calls = []

  done_thinking = False
  # accumulate the partial fields
  for chunk in stream:
    if chunk.message.thinking:
      thinking += chunk.message.thinking
      print(chunk.message.thinking, end='', flush=True)
    if chunk.message.content:
      if not done_thinking:
        done_thinking = True
        print('\n')
      content += chunk.message.content
      print(chunk.message.content, end='', flush=True)
    if chunk.message.tool_calls:
      tool_calls.extend(chunk.message.tool_calls)
      print(chunk.message.tool_calls)

  # append accumulated fields to the messages
  if thinking or content or tool_calls:
    messages.append({'role': 'assistant', 'thinking': thinking, 'content': content, 'tool_calls': tool_calls})

  if not tool_calls:
    break

  for call in tool_calls:
    if call.function.name == 'get_temperature':
      result = get_temperature(**call.function.arguments)
    else:
      result = 'Unknown tool'
    messages.append({'role': 'tool', 'tool_name': call.function.name, 'content': result})