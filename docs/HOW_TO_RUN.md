# How to Run Travel Agent

This guide outlines the steps to set up and run the Travel Agent Web UI and Backend.

## Prerequisites

1.  **Python 3.x**
2.  **Node.js & npm** (required for the frontend) - [Download Here](https://nodejs.org/)

## Steps to Run

### 1. Start the Backend (API)

Open a terminal in the project root (`<project_root>/TravelAgent`) and run:

```bash
uvicorn services.api:app --reload --port 8000
```

You should see output similar to: `Uvicorn running on http://0.0.0.0:8000`

### 2. Set Up and Start the Frontend

Open a **new terminal window**, navigate to the `frontend` directory, install dependencies, and start the development server:

```bash
cd <project_root>/TravelAgent/frontend
npm install
npm run dev
```

You should see output indicating the local server is running, typically: `Local: http://localhost:5173`

### 3. Use the App

Open your browser and navigate to **[http://localhost:5173](http://localhost:5173)**.

You can now chat with your agent!
- **Try:** "Find me cheapest flights from Delhi to Mumbai tomorrow"
- **Try:** "Find flights from London to Paris next week"

## Troubleshooting

- **Import Errors**: If you encounter errors related to `utils.prompts`, ensure your `services/api.py` and `utils/prompts.py` imports are up to date.
- **Node not found**: Ensure Node.js is installed and added to your system PATH.
