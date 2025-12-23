# Travel Agent PEAS Model

This document outlines the PEAS (Performance measure, Environment, Actuators, Sensors) characteristics for the AI Travel Agent.

## Overview

The Travel Agent is designed to assist users in finding flight and hotel options by interpreting natural language queries and interacting with travel APIs (Amadeus).

## PEAS Diagram

```mermaid
graph TD
    classDef main fill:#f9f,stroke:#333,stroke-width:2px;
    classDef perf fill:#d4edda,stroke:#155724,stroke-width:1px,color:#155724;
    classDef env fill:#cce5ff,stroke:#004085,stroke-width:1px,color:#004085;
    classDef act fill:#fff3cd,stroke:#856404,stroke-width:1px,color:#856404;
    classDef sens fill:#f8d7da,stroke:#721c24,stroke-width:1px,color:#721c24;

    TA((Travel Agent)):::main

    subgraph Performance [Performance Measures]
        direction TB
        P1(Accuracy of Search):::perf
        P2(Cost Optimization):::perf
        P3(Time Efficiency):::perf
        P4(User Satisfaction):::perf
        P5(Error Reliability):::perf
    end

    subgraph Environment [Environment]
        direction TB
        E1(User):::env
        E2(Amadeus API):::env
        E3(Python Runtime):::env
    end
    
    subgraph Actuators [Actuators]
        direction TB
        A1(API Requests):::act
        A2(Data Filtering/Sorting):::act
        A3(Response Gen):::act
    end

    subgraph Sensors [Sensors]
        direction TB
        S1(User Input):::sens
        S2(API Responses):::sens
        S3(System Clock):::sens
    end

    TA --> Performance
    TA --> Environment
    TA --> Actuators
    TA --> Sensors
```

## Detailed Breakdown

### 1. Performance Measure
The criteria used to evaluate the success of the agent's behavior:
- **Relevance**: Do the search results match the user's intent (origin, destination, dates)?
- **Optimization**: Ability to find the best value (cheapest price) or most convenient (fastest, non-stop) options.
- **Speed**: Low latency in processing requests and retrieving API data.
- **Reliability**: Graceful handling of API errors (e.g., 500 errors) and invalid user inputs.

### 2. Environment
The context in which the agent operates:
- **User**: The human providing natural language prompts (e.g., "Find me cheapest flights...").
- **Amadeus API**: The external service providing real-time flight and hotel data.
- **Digital Infrastructure**: The local Python environment.

### 3. Actuators
The mechanisms the agent uses to act upon the environment:
- **Search Queries**: Constructing and sending HTTP requests to Amadeus endpoints (`/v2/shopping/flight-offers`, `/v1/reference-data/locations/hotels/by-city`).
- **Data Processor**: Client-side logic to filter (e.g., by seats, stops) and sort (e.g., by price, duration) raw API data.
- **Output Interface**: Formatting the structured data into human-readable text or JSON for the user.

### 4. Sensors
The methods the agent uses to perceive the environment:
- **Input Receiver**: accepting strings from the command line or chat interface.
- **API Response Handler**: Parsing JSON responses, status codes, and error messages from Amadeus.
- **Time/Date functions**: Checking current system time to validate dates (e.g., ensuring departure is in the future).
