# Travel Agent

A sophisticated flight search agent that leverages Large Language Models (LLMs) to understand natural language queries, extract user intent, and interact with the Amadeus API to find the best flight options.

## Features & Capabilities

The agent has evolved to handle increasingly complex user requests, moving from simple date parsing to advanced intent understanding.

### Version 0: Explicit Date Parsing & Basic Search
**Expectation**: The agent handles precise, hardcoded dates provided by the user.
*   **Prompt**: "Book a flight between BLR(Bengaluru) on Dec 25th, 2026 to Bombay(Bom)."
*   **Capability**: Extracts `origin`, `destination`, and absolute `departure_date`.
*   **Implementation Milestones**:
    *   `4b16bfc`: Initial "flight gpt" setup.
    *   `5d7814e`: Introduced basic cheapest flight search functionality.

### Version 1: Relative Date Parsing & Standard Intent
**Expectation**: The agent interprets relative time expressions and splits intents.
*   **Prompt**: "Book a flight between BLR(Bengaluru) to Bombay(Bom) tomorrow."
*   **Capability**:
    *   Converts "tomorrow" (or "next Friday") to `YYYY-MM-DD`.
    *   Differentiates between standard (specific date) and advanced (flexible/cheapest) intents.
*   **Implementation Milestones**:
    *   `37e0210`: Refactored intent handling to differentiate standard vs advanced queries.
    *   `4cc204b`: Added flight inspiration search and refactored cheapest flight logic.

### Version 1.1: Flexible Date Ranges & Intents
**Expectation**: The agent handles broad timeframes, contextual date ranges, and ambiguity.
*   **Prompt**: "Plan a trip from BLR to BOM next month."
*   **Capability**:
    *   **Intent Detection**: Identifies `intent` (Standard vs Advanced) and presence of `date_range`.
    *   **Range Extraction**: Parses "next month" into `start_date` and `end_date` (e.g., `2026-01-01` to `2026-01-31`).
    *   **Structured Output**: Returns a `DateRangeDetails` object.
*   **Implementation Milestones**:
    *   `549d684`: Implemented date range detection for flight search intent.
    *   `2ae9801`: Introduced `DateRangeDetails` schema.
    *   `72eaf90`: Enhanced intent fetching with date range details and multicity detection.

### Version 1.2: Advanced Constraints & Sorting
**Expectation**: The agent respects user preferences for pricing, duration, and comfort.
*   **Prompt**: "Find the cheapest flight from BLR to BOM next weekend."
*   **Capability**:
    *   **Sorting**: Extracts `sorting_details` (e.g., "price").
    *   **Advanced Intent**: Maps to `find_flights_advanced`.
    *   **Complex Parsing**: Combines date range ("next weekend") with sorting ("cheapest") in a single pass.
*   **Implementation Milestones**:
    *   `7250414`: Enhanced search with client-side filtering and sorting options.
    *   `0345dbc`: Connected advanced search with client-side filters to GPT service.
    *   `e8a7cd0`: Added sorting preference to intent fetching schema (`sorting_details`).

---

## Future Roadmap & Brainstorming

We are actively exploring new agents and workflows to expand the Travel Agent's utility.

### 1. Multi-Modal Booking Agents
Expand beyond flights to complete the travel experience.
*   **Hotel Search Agent**: Triggered after flight booking to find accommodation.
*   **Car Rental/Transfer Agent**: Assist with ground transportation.

### 2. Itinerary & Planning Agents

*   **Multi-City / Round-the-World Agent**: Handle complex routing like "London -> Tokyo -> Sydney -> LA -> London".
    *   *Foundation Laid*: `72eaf90` added `multicity_trip` to intent schema.
*   **Round-the-World Agent**: Handle complex routing like "London -> Tokyo -> Sydney -> LA -> London".
    *   *Foundation Laid*: `72eaf90` added `round_the_world_trip` to intent schema.

### 3. Budget & Deal Hunting Agents
*   **"Anywhere" / Inspiration Agent**: Suggest destinations based on budget and themes (e.g., "Beach under $1000").
*   **Price Watch Agent**: Periodically check for price drops on specific routes.

### 5. Orchestrator Workflow (The "Super Agent")
A central "Triage Agent" to coordinate complex requests (e.g., "Plan a honeymoon") by delegating to specialized Flight, Hotel, and Activity agents.