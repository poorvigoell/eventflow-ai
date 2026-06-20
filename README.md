# EventFlow AI 🚦

EventFlow AI is an advanced, AI-powered traffic prediction and simulation dashboard designed to forecast and mitigate urban congestion caused by major public events. It uses machine learning to predict traffic buildup, simulates real-time traffic anomalies, and generates tactical dispatch plans for city management and law enforcement.

## Key Features

*   **Predictive Analytics:** Uses an XGBoost model to predict total traffic incidents, phase timelines (inflow, steady, exodus), and peak congestion hours based on event type, duration, location, and weather.
*   **Live Traffic Dashboard:** An interactive map overlay using Leaflet and TomTom API to visualize live traffic flows, high-risk junctions, and dynamically generated road congestion.
*   **Tactical Response Planning:** Automatically generates resource dispatch recommendations (police, ambulances, tow trucks) and computes the economic impact of gridlocks.
*   **Signal Optimization (Digital Twin):** Simulates a Reinforcement Learning (RL) agent that monitors queue lengths and dynamically adjusts green-light splits to alleviate traffic bottlenecks.
*   **Real-time Anomaly Injection:** Simulate traffic chaos (accidents, emergency vehicles stuck) and broadcast alerts to the frontend via WebSockets in real-time.
*   **Crowd Dispersal Mapping:** Visualizes how crowds and traffic will organically disperse into the city grid post-event.

## Technology Stack

**Frontend:**
*   React (Vite)
*   Tailwind CSS (Styling)
*   React-Leaflet (Map Integration)
*   Recharts (Data Visualization)
*   Lucide React (Icons)

**Backend:**
*   Python (FastAPI)
*   Uvicorn (Asynchronous ASGI server)
*   XGBoost & Scikit-learn (Machine Learning)
*   OSMnx & NetworkX (Graph/Spatial Data)
*   WebSockets (Live Alerts)

## Getting Started

### Prerequisites
Make sure you have Node.js and Python 3.9+ installed.

### 1. Backend Setup
1. Navigate to the root directory.
2. Create and activate a virtual environment (optional but recommended).
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI backend server:
   ```bash
   python -m uvicorn api.main:app --reload --port 8000
   ```

### 2. Frontend Setup
1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install the Node modules:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```

### 3. Environment Variables
If you intend to use live TomTom traffic data, you will need to add a `.env` file in the root directory containing your API key:
```env
TOMTOM_API_KEY=your_tomtom_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

## How to Use
1. Open the frontend URL provided by Vite (usually `http://localhost:5173`).
2. **Drop a Pin**: Click anywhere on the map to select an event location.
3. **Configure Event**: Set the event type, duration, weather conditions, etc., in the left sidebar.
4. **Predict**: Click "Run Predictive Analysis" to generate the data.
5. **Explore Tabs**: Navigate through the Live Dashboard, Tactical Plan, Signals, and Digital Twin tabs to explore the AI's recommendations.
6. **Simulate Chaos**: Go to the "Live Alerts" tab and click "Simulate Chaos" to inject random traffic anomalies into the dashboard in real-time!

## License
This project is for demonstration and portfolio purposes.
