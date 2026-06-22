"""
Multi-Agent Reinforcement Learning (MARL) Environment for Cooperative Traffic Signals.

Each of the N traffic signal agents operates independently but communicates
with physically adjacent neighbors via learned message vectors. Agents share
a cooperative reward that prevents selfish optimization.

Architecture:
    - Decentralized execution: each agent sees only its own state + neighbor messages
    - Centralized training: a single PPO model is trained on all agents' experiences
    - Parameter sharing: one neural network is instantiated for all agents
    - Message passing: agents output a 4-float message vector delivered to neighbors
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import math
import random

from models.predict import predict_event_impact
import graph.simulator as sim


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
NUM_AGENTS = 5
MESSAGE_DIM = 4          # learned message vector size per agent
MAX_NEIGHBORS = 4        # max neighbors any agent can have (for padding)
OBS_DIM_PER_AGENT = 15   # own state (11) + incoming messages (4)
ACTION_CHOICES = 5        # [-10, -5, 0, +5, +10] seconds adjustment


class MARLTrafficEnv(gym.Env):
    """
    Multi-agent Gymnasium environment where N traffic signal agents
    cooperate through explicit message-passing over a dynamic road topology.
    
    For compatibility with stable-baselines3, the environment exposes a
    *flattened* single-agent interface:
        observation: Box(NUM_AGENTS * OBS_DIM_PER_AGENT)
        action:      MultiDiscrete([ACTION_CHOICES] * NUM_AGENTS)
        reward:      scalar (sum of per-agent rewards)
    
    Internally, it maintains per-agent state, adjacency, and message buffers.
    """

    metadata = {"render_modes": []}

    def __init__(self, G=None, config=None, training_mode=False):
        super().__init__()

        self.G = G
        self.config = config or {}
        self.num_agents = NUM_AGENTS
        self.training_mode = training_mode

        # --- Spaces (flattened for SB3 compatibility) ---
        self.observation_space = spaces.Box(
            low=-1.0, high=1.0,
            shape=(NUM_AGENTS * OBS_DIM_PER_AGENT,),
            dtype=np.float32,
        )
        self.action_space = spaces.MultiDiscrete([ACTION_CHOICES] * NUM_AGENTS)

        # --- Simulation parameters ---
        self.max_steps = 120          # 2 hours at 1-min intervals
        self.current_step = 0
        self.base_green_time = 45.0

        # --- Message buffers (agent_i -> 4-float vector) ---
        # Updated externally by the wrapper / policy after each step
        self.message_buffer = np.zeros((NUM_AGENTS, MESSAGE_DIM), dtype=np.float32)

        # --- Adjacency (computed on reset) ---
        self.adjacency = [[False] * NUM_AGENTS for _ in range(NUM_AGENTS)]
        self.adj_distances = [[-1.0] * NUM_AGENTS for _ in range(NUM_AGENTS)]

        # --- Load historical dataset for sampling ---
        self.dataset = None
        try:
            import pandas as pd
            dataset_path = 'C:/Users/poorv/Downloads/Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv'
            df = pd.read_csv(dataset_path)
            valid_types = ["protest", "public_event", "sports", "vip_movement", "procession"]
            self.dataset = df[df['event_cause'].isin(valid_types)].dropna(subset=['latitude', 'longitude'])
        except Exception as e:
            print(f"MARL env running without historical dataset: {e}")

        self._setup_event()

    # ------------------------------------------------------------------
    # Event & Junction Setup
    # ------------------------------------------------------------------

    def _setup_event(self):
        """Configure event parameters and discover junctions."""
        if self.dataset is not None and not self.dataset.empty and not self.config:
            row = self.dataset.sample(1).iloc[0]
            self.lat = float(row['latitude'])
            self.lng = float(row['longitude'])
            cause = row['event_cause']
            if cause == 'procession':
                cause = 'protest'
            self.event_type = cause
            self.duration_hours = random.uniform(1.0, 4.0)
            self.rain = random.choice([True, False])
            try:
                import pandas as pd
                start_dt = pd.to_datetime(row['start_datetime'])
                self.start_hour = start_dt.hour
            except Exception:
                self.start_hour = random.randint(8, 20)
        else:
            self.lat = self.config.get('latitude', 12.9789)
            self.lng = self.config.get('longitude', 77.5998)
            self.event_type = self.config.get(
                'event_type',
                random.choice(["protest", "public_event", "sports", "vip_movement"]),
            )
            self.duration_hours = self.config.get('duration_hours', 2.0)
            self.rain = self.config.get('weather_rain', random.choice([True, False]))
            self.start_hour = self.config.get('start_hour', random.randint(8, 20))

        # Baseline prediction to seed queues
        if getattr(self, 'training_mode', False):
            self.total_incidents = 150.0 * (1.5 if self.rain else 1.0)
        else:
            try:
                pred = predict_event_impact(
                    event_type=self.event_type,
                    latitude=self.lat,
                    longitude=self.lng,
                    zone="Central",
                    start_time=f"2024-05-01 {self.start_hour:02d}:00:00",
                    duration_hours=self.duration_hours,
                )
                self.total_incidents = pred['total_incidents'] * (1.5 if self.rain else 1.0)
            except Exception as e:
                print(f"Warning: predict_event_impact failed, using fallback: {e}")
                self.total_incidents = 150.0 * (1.5 if self.rain else 1.0)

        # Discover junctions from the road graph
        if self.G:
            try:
                high_risk = sim.get_high_risk_junctions_graph(
                    self.G, self.lat, self.lng,
                    self.total_incidents,
                    max_junctions=self.num_agents,
                )
            except Exception:
                high_risk = []
        else:
            high_risk = []

        # Fallback synthetic junctions
        if len(high_risk) < self.num_agents:
            high_risk = []
            names = [
                "Main Gate Junction", "North Exit Road",
                "East Corridor", "South Bypass", "Outer Ring Connect",
            ]
            for i in range(self.num_agents):
                high_risk.append({
                    "name": names[i],
                    "risk_score": max(0.1, 0.8 - i * 0.1),
                    "centrality": max(0.01, 0.1 - i * 0.02),
                })

        self.junctions = high_risk[:self.num_agents]

        # --- Compute real adjacency from the road graph ---
        if self.G and all('u' in j for j in self.junctions):
            try:
                self.adjacency, self.adj_distances = sim.compute_junction_adjacency(
                    self.G, self.junctions, max_dist_m=500,
                )
            except Exception as e:
                print(f"Adjacency computation failed, using synthetic: {e}")
                self._build_synthetic_adjacency()
        else:
            self._build_synthetic_adjacency()

    def _build_synthetic_adjacency(self):
        """
        Fallback: build adjacency from a corridor topology where each
        junction connects to its immediate neighbors (J0-J1-J2-J3-J4).
        Plus a shortcut edge J0-J2 to make the graph non-trivially linear.
        """
        n = self.num_agents
        self.adjacency = [[False] * n for _ in range(n)]
        self.adj_distances = [[-1.0] * n for _ in range(n)]
        for i in range(n - 1):
            self.adjacency[i][i + 1] = True
            self.adjacency[i + 1][i] = True
            self.adj_distances[i][i + 1] = 300.0
            self.adj_distances[i + 1][i] = 300.0
        # Shortcut
        if n > 2:
            self.adjacency[0][2] = True
            self.adjacency[2][0] = True
            self.adj_distances[0][2] = 450.0
            self.adj_distances[2][0] = 450.0

    # ------------------------------------------------------------------
    # Gymnasium Interface
    # ------------------------------------------------------------------

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        if options and 'config' in options:
            self.config = options['config']

        self._setup_event()
        self.current_step = 0

        # Per-agent state
        self.green_times = np.full(self.num_agents, self.base_green_time)
        self.queues = np.zeros(self.num_agents)
        for i, j in enumerate(self.junctions):
            self.queues[i] = (self.total_incidents * 0.5) * j.get('risk_score', 0.5)

        self.crowd_remaining = 1.0

        # Clear message buffers
        self.message_buffer = np.zeros((self.num_agents, MESSAGE_DIM), dtype=np.float32)

        # Per-agent reward tracking (for API to expose)
        self.last_rewards = np.zeros(self.num_agents)

        return self._get_flat_obs(), {}

    def step(self, action):
        """
        action: array of shape (NUM_AGENTS,) with values in [0, ACTION_CHOICES-1]
        Maps to adjustments: [-10, -5, 0, +5, +10]
        """
        self.current_step += 1

        # Decode actions → adjustments
        adjustment_map = {0: -10.0, 1: -5.0, 2: 0.0, 3: 5.0, 4: 10.0}
        adjustments = np.array([adjustment_map[int(a)] for a in action])

        # Apply adjustments
        self.green_times += adjustments

        # Safety clipping
        violations = np.zeros(self.num_agents)
        for i in range(self.num_agents):
            if self.green_times[i] < 10.0:
                self.green_times[i] = 10.0
                violations[i] = 1
            elif self.green_times[i] > 90.0:
                self.green_times[i] = 90.0
                violations[i] = 1

        # --- Simulate traffic flow ---
        tau = 30.0
        prev_crowd = self.crowd_remaining
        self.crowd_remaining = math.exp(-self.current_step / tau)
        arriving_crowd_pct = prev_crowd - self.crowd_remaining
        total_arrivals = arriving_crowd_pct * self.total_incidents * 3.0

        for i, j in enumerate(self.junctions):
            arrivals = total_arrivals * j.get('risk_score', 0.5)
            green_ratio = self.green_times[i] / 100.0
            cleared = green_ratio * 40.0 * (0.7 if self.rain else 1.0)
            self.queues[i] = max(0.0, self.queues[i] + arrivals - cleared)

        # --- Compute per-agent rewards ---
        avg_queue_global = float(np.mean(self.queues))
        global_reward = -(avg_queue_global / 100.0)

        agent_rewards = np.zeros(self.num_agents)
        for i in range(self.num_agents):
            # Local component
            local_reward = -(self.queues[i] / 100.0)

            # Green wave bonus: if I pushed cars (+green) and my neighbor has low queue
            green_wave_bonus = 0.0
            for k in range(self.num_agents):
                if self.adjacency[i][k] and self.queues[k] < 50 and adjustments[i] > 0:
                    green_wave_bonus += 0.5

            # Cooperative reward
            agent_rewards[i] = (
                0.7 * local_reward
                + 0.3 * global_reward
                + green_wave_bonus
                - 5.0 * violations[i]
            )

            # Bonus for clearing own queue
            if self.queues[i] < 20.0:
                agent_rewards[i] += 2.0

        self.last_rewards = agent_rewards.copy()

        # Scalar reward for SB3 (sum of all agent rewards)
        total_reward = float(np.sum(agent_rewards))

        done = self.current_step >= self.max_steps or self.crowd_remaining < 0.05

        info = {
            "avg_queue": avg_queue_global,
            "per_agent_rewards": agent_rewards.tolist(),
            "per_agent_queues": self.queues.tolist(),
            "violations": violations.tolist(),
            "adjustments": adjustments.tolist(),
        }

        return self._get_flat_obs(), total_reward, bool(done), False, info

    # ------------------------------------------------------------------
    # Observations
    # ------------------------------------------------------------------

    def _get_agent_obs(self, agent_id):
        """Build the observation vector for a single agent."""
        obs = np.zeros(OBS_DIM_PER_AGENT, dtype=np.float32)

        # [0] Own green time (normalized 0–120s)
        obs[0] = self.green_times[agent_id] / 120.0

        # [1] Own queue (normalized ~0–1000)
        obs[1] = min(1.0, self.queues[agent_id] / 1000.0)

        # [2] Own centrality
        obs[2] = float(self.junctions[agent_id].get('centrality', 0.05))

        # [3] Crowd remaining
        obs[3] = self.crowd_remaining

        # [4–5] Time of day (sin/cos)
        curr_hour = self.start_hour + (self.current_step / 60.0)
        obs[4] = math.sin(2 * math.pi * curr_hour / 24.0)
        obs[5] = math.cos(2 * math.pi * curr_hour / 24.0)

        # [6] Rain
        obs[6] = 1.0 if self.rain else 0.0

        # [7–10] Event type one-hot
        types = ["protest", "public_event", "sports", "vip_movement"]
        idx = types.index(self.event_type) if self.event_type in types else 1
        obs[7 + idx] = 1.0

        # [11–14] Incoming messages from neighbors (averaged if multiple)
        neighbor_msgs = []
        for k in range(self.num_agents):
            if self.adjacency[agent_id][k]:
                neighbor_msgs.append(self.message_buffer[k])

        if neighbor_msgs:
            avg_msg = np.mean(neighbor_msgs, axis=0)
        else:
            avg_msg = np.zeros(MESSAGE_DIM, dtype=np.float32)
        obs[11:15] = avg_msg

        return obs

    def _get_flat_obs(self):
        """Concatenate all agent observations into a single vector."""
        all_obs = []
        for i in range(self.num_agents):
            all_obs.append(self._get_agent_obs(i))
        return np.concatenate(all_obs).astype(np.float32)

    # ------------------------------------------------------------------
    # Message Passing Interface
    # ------------------------------------------------------------------

    def set_messages(self, messages):
        """
        Called externally (by the MARL wrapper / policy) to update the
        message buffer after the network's MessageHead has produced outputs.
        
        messages: np.array of shape (NUM_AGENTS, MESSAGE_DIM)
        """
        self.message_buffer = np.array(messages, dtype=np.float32)

    def get_adjacency(self):
        """Return the adjacency matrix for the frontend to visualize."""
        return self.adjacency

    def get_neighbors(self, agent_id):
        """Return list of neighbor agent indices."""
        return [k for k in range(self.num_agents) if self.adjacency[agent_id][k]]
