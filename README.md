# EventFlow — AI-Powered Urban Traffic Management

EventFlow is a full-stack, AI-powered urban traffic prediction and management platform built for Bengaluru, India. It enables traffic police, city administrators, and event organisers to **forecast the traffic impact of large public events before they happen**, and then manage resulting congestion through intelligent signal optimization, tactical resource dispatch, crowd dispersal simulation, and post-event causal learning.

## Key Features

### Crowd Dispersal Kinematics & Geospatial Heatmapping
- The `dispersal_sim.py` module computes the nearest NetworkX edge based on the venue's Haversine coordinates and executes shortest-path radial traversals (via Dijkstra) outward up to a 3km maximum threshold. It mathematically simulates human kinematics by projecting movement at a constant 3 km/h (0.05 km/min). Density is modeled via an active temporal exponential decay function `e^(-λt)` applied to the absolute crowd size, tapering the density metric as time increments. It packages these localized high-density coordinate payloads and broadcasts them to the React frontend, where `React-Leaflet` maps them into a fluid HeatmapLayer over time.

### Economic Scoring & Logistic Mode Split
- The `economic_scorer.py` computes a normalized `0.0` to `1.0` float by fusing two vectors: an intrinsic event baseline weight (e.g., VIP movements = 0.9, Protests = 0.2) and a spatial geospatial modifier generated via OSMnx point-of-interest mapping (e.g., proximity to tech parks acts as a positive scalar). Based on this final float, the algorithm segments the crowd volume into "Premium", "Middle", and "Mass" bins using hard thresholds. These bins act as probability modifiers to calculate the exact percentage split for likely transport modes, dynamically weighting the pressure on local Metro stations versus arterial road cab bottlenecks.

### Causal Data Synthetic Augmentation (Unconfoundedness Injection)
- Because true randomized control trials (RCTs) are impossible in live traffic, `augment_causal_data.py` synthetically retrofits the historical dataset. It uses logit-based probabilities to simulate "treatment assignments" (like deploying barricades). Crucially, it purposefully injects unobserved confounders to mimic real-world police deployment bias (e.g., forcing a high mathematical probability that severe, high-priority events receive barricades, while minor events do not). A `ColumnTransformer` preprocessing pipeline then normalizes this data to mathematically enforce the **Strict Unconfoundedness** assumption required by the T-Learner architecture.

### Penalized Dijkstra Routing for Diversions
- When an event triggers a tactical plan, the backend queries the OSMnx/NetworkX graph of the Bengaluru road network. Rather than finding the shortest geometric path, it executes a **Penalized Dijkstra** algorithm. It actively identifies the specific edges (roads) inside the predicted "Impact Zone" and artificially multiplies their travel-time weights by an `8x` scalar penalty. When the shortest-path algorithm runs, it mathematically naturally routes *around* the inflated edges, automatically generating safe, optimal diversion paths that completely bypass the predicted gridlock epicenter.

### Predictive Analytics & Feature Engineering
- Powered by an XGBoost 3-Phase Prediction engine trained on real anonymized Bengaluru event-incident data. It automatically decomposes predictions into **Inflow → Steady → Exodus** phases with per-phase peak hours utilizing 12 engineered features including cyclical time encoding (`hour_sin`, `hour_cos`), rush-hour flags, and weekend flags.

### Adaptive Signal Control (Webster & MARL)
- The system utilizes a Webster Formula baseline (`g_i = (y_i / Y) × (C - L)`) to compute optimal static green splits. For dynamic routing, an Adaptive AI Engine automatically boots either a Single-Agent RL (PPO) for localized congestion, or a **MARL Cooperative Network** for multi-junction cascading gridlock—where 5 independent agents communicate via a decentralized partially observable Markov decision process (Dec-POMDP) to coordinate network-wide signal phases.

### Real-Time Anomaly Alerts & AI Operator
- WebSockets aggressively broadcast live traffic anomalies to all connected clients. A Groq-powered LLM agent (LLaMA 3.3 70B) with tool-calling capabilities (geocode, analyze event, trigger anomaly) streams results via Server-Sent Events (SSE), dynamically mutating the React state so the map, KPIs, and prediction data update live as the AI executes context-aware commands.

### The Autonomous RL Feedback Loop (Continuous Online Learning)
- Once the `EconML` T-Learner calculates the exact Individual Treatment Effect (ITE) of a resolved incident, the FastAPI backend instantly spawns an asynchronous `BackgroundTask`. This thread acquires a strict mutual-exclusion `threading.Lock` to prevent database race conditions and silently boots a headless `EventFlowEnv` Gymnasium environment. It executes a targeted Proximal Policy Optimization (PPO) micro-training session where the ITE mathematical output directly overrides the agent's reward penalty function. The newly optimized weights are then hot-swapped and permanently saved into the active `ppo_eventflow.zip` checkpoint. This enables true **Continuous Online Learning** without ever disrupting the live WebSocket server.

### Algorithmic Client-Side Raster Manipulation (`FilteredTrafficLayer`)
- Instead of blindly rendering TomTom API map tiles, the React frontend intercepts the raw raster images and passes them through an HTML5 `<canvas>` manipulation pipeline. The `FilteredTrafficLayer` utilizes `getImageData()` to mathematically iterate over the `Uint8ClampedArray` (RGBA matrix) of every single tile. It executes a strict algorithmic filter (`g > 80 && g > r * 1.3 && g > b * 1.3`) to identify and strip out pixels where green dominates (free-flowing traffic). By converting these specific pixels to an alpha-0 transparency, the CartoDB dark basemap is allowed to bleed through, ensuring the UI *only* highlights active congestion (orange/red anomalies) to dramatically reduce cognitive load.

### Asynchronous Paced Tile Queuing (Strict Rate Limiting)
- Because Leaflet aggressively fetches 15-20 tiles simultaneously during a map pan, it easily triggers `HTTP 429 Too Many Requests` API lockouts from TomTom's 5 QPS (Queries Per Second) limit. To bypass this, the frontend utilizes a custom `tileQueue` manager. It decouples Leaflet’s render cycle from the actual network stack, pushing all tile requests into an async array. The processing loop utilizes JavaScript `Promises` and `await new Promise(r => setTimeout(r, 250))` to enforce a mathematically perfect, absolute ceiling of **4 Requests Per Second**. If a request still fails, the custom `ThrottledTrafficLayer` silently resolves an empty transparent canvas instead of throwing a broken DOM `<img>` icon.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite |
| Maps | React-Leaflet + CartoDB Dark Tiles + HTML5 Canvas |
| Charts | Recharts |
| Backend | FastAPI + Uvicorn (Python) |
| ML — Prediction | XGBoost / GradientBoostingRegressor |
| ML — Causal Inference | Do-Calculus T-Learner (Microsoft EconML) |
| RL — Single Agent | Stable-Baselines3 PPO + Gymnasium |
| RL — MARL | Custom Dec-POMDP multi-agent PPO with message-passing |
| Graph Engine | OSMnx + NetworkX |
| Live Traffic | TomTom Traffic Flow API (with Custom Paced Queue) |
| LLM | Groq Cloud (LLaMA 3.3 70B) |
| Real-Time | WebSockets + Server-Sent Events (SSE) |

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
