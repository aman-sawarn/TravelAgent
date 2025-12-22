
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app

def run_test(query, description):
    print(f"\n{'='*50}")
    print(f"TEST: {description}")
    print(f"Query: {query}")
    print(f"{'='*50}")
    
    init_state = {
        "user_query": query,
        "response": None,
        "action": None,
        "action_input": None,
        "results": None,
        "itinerary": None,
    }

    try:
        output = app.invoke(init_state)
        print("\n--- Final State Results ---")
        results = output.get("results")
        if results:
            if isinstance(results, list) and results and "warning" in results[0]:
                 print(f"Result Type: WARNING/ERROR - {results[0]}")
            elif isinstance(results, dict) and "source" in results and results["source"] == "amadeus_mock":
                 print(f"Result Type: MOCK DATA (Success) - {results['warning']}")
                 print(f"Data Sample: {results['results']['data'][0]}")
            elif isinstance(results, list):
                 print(f"Result Type: FLIGHT OFFERS (Success) - Found {len(results)} offers")
            else:
                 print(f"Result Type: {type(results)}")
                 print(results)
        else:
            print("No results found.")
            
        print("\n--- Assistant Response ---")
        print(output.get("response"))
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    # 1. Standard Search
    run_test(
        "Find flights from BLR to DEL on 2025-12-25 for 1 adult.", 
        "Standard Flight Search (BLR -> DEL)"
    )

    # 2. Cheapest Date Search (Route)
    # Using a route likely to fail in Test Env (return 500) but verifies the code path
    run_test(
        "Find cheapest flights from LON to PAR.", 
        "Cheapest Route Search (LON -> PAR)"
    )

    # 3. Inspiration Search (Cheapest to Anywhere)
    # This should hit the Mock Fallback
    run_test(
        "Find cheapest flights from MAD.", 
        "Inspiration Search (MAD -> Anywhere)"
    )
