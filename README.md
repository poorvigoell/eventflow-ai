# EventFlow — AI-Powered Urban Traffic Management

EventFlow is a full-stack, AI-powered urban traffic prediction and management platform built for Bengaluru, India. It enables traffic police, city administrators, and event organisers to **forecast the traffic impact of large public events before they happen**, and then manage resulting congestion through intelligent signal optimization, tactical resource dispatch, crowd dispersal simulation, and post-event causal learning.

## Key Features

### Predictive Analytics
- **XGBoost 3-Phase Prediction** trained on real anonymised Bengaluru event-incident data
- Decomposes predictions into **Inflow → Steady → Exodus** phases with per-phase peak hours
- 12 engineered features including cyclical time encoding (`hour_sin`, `hour_cos`), rush-hour flag, and weekend flag
- Confidence score and feature importance displayed per prediction

### Live Traffic Dashboard
- Interactive **Leaflet map** with dark CartoDB tiles and event venue pin
- **TomTom Live Traffic overlay** — fetches real-time speed and congestion for the 5 nearest arterial roads, rendered as colour-coded dashed polylines (free / moderate / congested)
- **30-minute client-side cache** for all live traffic and prediction data — survives page reloads without redundant API calls
- **Emergency Hospital Route Toggle** — show/hide NHS hospital routing overlays on the live map

### Tactical Response Planning
- Automated manpower deployment planner using **OSMnx edge betweenness centrality** to identify the top 5 critical junctions
- Auto-computes exact counts of police, patrol vehicles, ambulances, tow trucks, and barricade teams scaled to predicted severity
- Barricade protocol with timed deployment orders
- Diversion routing via **penalised Dijkstra** (8× travel time on high-risk edges)

### Adaptive Signal Control
- **Webster Formula baseline** — computes optimal static green splits using `g_i = (y_i / Y) × (C - L)` for all predicted high-risk junctions
- **Adaptive AI Engine** — automatically selects the best controller for each scenario:
  - **Single-Agent RL (PPO)** for localised, single-junction congestion — fast, focused signal adjustment
  - **MARL Cooperative Network** for multi-junction cascading gridlock — 5 independent agents communicate via message-passing to coordinate across the road network
- Real-time **Agent Communication Network** graph visualisation with live queue pressure rings
- Per-agent junction cards showing green time, queue length, and adjustment delta

### Post-Event Causal Autopsy
- **Do-Calculus T-Learner** (Microsoft EconML) computes the **Individual Treatment Effect (ITE)** of each tactical deployment
- Isolates exactly how many minutes barricades and diversions saved (or cost), controlling for confounders: event priority, event type, time of day, and location
- Trained on synthetically augmented causal dataset generated from the same real Bengaluru data — capped to realistic clearance times to prevent extreme predictions
- Works on both resolved live anomalies and historical mock events

### Crowd Dispersal Simulation
- Monte Carlo heatmap snapshots at 5-minute intervals post-event
- Timeline scrubber to watch crowd density decay toward metro stations, bus stops, and parking facilities
- Economic segment analysis and transport mode split (metro vs. cab)

### Real-Time Anomaly Alerts
- WebSocket broadcast of live traffic anomalies to all connected clients simultaneously
- **Simulate Chaos** button — inject random accidents and emergency events in real-time
- Emergency ETA calculations for ambulances, fire trucks, and police based on jam factors
- Graph-based emergency routing via OSMnx from nearest hospital/station to venue

### AI Operator (Natural Language)
- Groq-powered LLM agent (LLaMA 3.3 70B) with tool-calling: geocode, analyse event, trigger anomaly
- Streams results via Server-Sent Events (SSE) — the map, KPIs, and prediction data update live as the AI executes
- Multi-turn conversation with full history tracking

### Digital Twin
- Side-by-side ML Predicted vs. Ground Truth map comparison
- Assesses historical model accuracy on resolved incidents

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite |
| Maps | React-Leaflet + CartoDB Dark Tiles |
| Charts | Recharts |
| Backend | FastAPI + Uvicorn (Python) |
| ML — Prediction | XGBoost / GradientBoostingRegressor |
| ML — Causal Inference | Custom T-Learner (GradientBoostingRegressor) |
| RL — Single Agent | Stable-Baselines3 PPO + Gymnasium |
| RL — MARL | Custom multi-agent PPO with message-passing |
| Graph Engine | OSMnx + NetworkX |
| Live Traffic | TomTom Traffic Flow API |
| LLM | Groq Cloud (LLaMA 3.3 70B) |
| Real-Time | WebSockets |

---

## Getting Started

### Prerequisites
Make sure you have **Node.js** and **Python 3.11 or 3.12** installed.

> [!WARNING]
> Do **NOT** use Python 3.13. The Reinforcement Learning libraries (`stable-baselines3`, `PyTorch`) currently do not have pre-built wheels for Python 3.13 and will fail to install.

### 1. Automated Backend Setup (Recommended)

The setup scripts handle everything automatically: create a virtual environment, install all ML libraries, generate the local causal training dataset, and retrain all models natively so they match your exact environment (preventing pickle/numpy version mismatch errors).

**Windows:**
```cmd
.\setup.bat
```
Once complete, start the backend:
```cmd
call venv\Scripts\activate.bat
set OMP_NUM_THREADS=1
python -m uvicorn api.main:app --reload --port 8000
```

**macOS / Linux:**
```bash
bash setup.sh
```
Once complete, start the backend:
```bash
source .venv/bin/activate
OMP_NUM_THREADS=1 python -m uvicorn api.main:app --reload --port 8000
```
> `OMP_NUM_THREADS=1` is required to prevent PyTorch deadlocks on macOS.

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Environment Variables
Create a `.env` file in the project root:
```env
TOMTOM_API_KEY=your_tomtom_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

---

## How to Use

1. **Open** `http://localhost:5173` in your browser.
2. **Drop a Pin** — click anywhere on the map to select an event location.
3. **Configure Event** — set event type, duration, weather, and priority in the left sidebar.
4. **Predict** — click "Run Predictive Analysis" to generate the full ML prediction.
5. **Explore Tabs:**
   - **Live Dashboard** — interactive map with TomTom live traffic, KPI cards, and AI Operator chat
   - **Tactical Plan** — auto-generated manpower deployment, barricade protocol, and diversion routes
   - **Signals** — Webster baseline or deploy the Adaptive AI Agent (RL/MARL auto-selected)
   - **Crowd Dispersal** — heatmap timeline of post-event crowd movement
   - **Digital Twin** — predicted vs. actual ground truth map comparison
   - **Live Alerts** — real-time WebSocket anomaly feed; click "Simulate Chaos" to inject events
   - **Causal Autopsy** — run post-event ITE analysis on resolved incidents

---

## License
This project is for demonstration and academic purposes.