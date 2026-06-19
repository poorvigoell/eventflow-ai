import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
import random
import math

from models.predict import predict_event_impact
import graph.simulator as sim

class EventFlowEnv(gym.Env):
    """
    Gymnasium environment simulating traffic intersections around an event venue.
    """
    def __init__(self, G=None, config=None):
        super(EventFlowEnv, self).__init__()
        
        self.G = G
        self.config = config or {}
        
        # 5 junctions, each can adjust green time by: -5s, 0s, +5s
        # 3 discrete actions per junction
        self.num_junctions = 5
        self.action_space = spaces.MultiDiscrete([3] * self.num_junctions)
        
        # State vector: 23 features
        # 5 junction green times (normalized 0-1) [0 to 120s]
        # 5 junction queue lengths (normalized 0-1) [0 to 1000 vehicles]
        # 5 junction centralities (0-1)
        # 1 crowd remaining % (0-1)
        # 2 time of day (sin, cos)
        # 1 rain flag (0 or 1)
        # 4 event type one-hot
        self.observation_space = spaces.Box(low=-1.0, high=1.0, shape=(23,), dtype=np.float32)
        
        self.max_steps = 120 # 2 hours simulated at 1-min intervals
        self.current_step = 0
        
        self.base_green_time = 45.0
        
        # Load event setup
        self._setup_event()
        
    def _setup_event(self):
        # Pick random config if not provided
        self.lat = self.config.get('latitude', 12.9789)
        self.lng = self.config.get('longitude', 77.5998)
        self.event_type = self.config.get('event_type', random.choice(["protest", "public_event", "sports", "vip_movement"]))
        self.duration_hours = self.config.get('duration_hours', 2.0)
        self.rain = self.config.get('weather_rain', random.choice([True, False]))
        self.start_hour = self.config.get('start_hour', random.randint(8, 20))
        
        # Get baseline prediction to seed queues
        pred = predict_event_impact(
            event_type=self.event_type,
            latitude=self.lat,
            longitude=self.lng,
            zone="Central",
            start_time=f"2024-05-01 {self.start_hour:02d}:00:00",
            duration_hours=self.duration_hours
        )
        self.total_incidents = pred['total_incidents'] * (1.5 if self.rain else 1.0)
        
        # Setup junctions
        if self.G:
            try:
                high_risk = sim.get_high_risk_junctions_graph(self.G, self.lat, self.lng, self.total_incidents, max_junctions=self.num_junctions)
            except:
                high_risk = []
        else:
            high_risk = []
            
        # Fallback synthetic junctions
        if len(high_risk) < self.num_junctions:
            base_risk = 0.8
            high_risk = []
            names = ["Main Gate Junction", "North Exit Road", "East Corridor", "South Bypass", "Outer Ring Connect"]
            for i in range(self.num_junctions):
                high_risk.append({
                    "name": names[i],
                    "risk_score": max(0.1, base_risk - i*0.1),
                    "centrality": max(0.01, 0.1 - i*0.02)
                })
                
        self.junctions = high_risk[:self.num_junctions]
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        if options and 'config' in options:
            self.config = options['config']
            self._setup_event()
            
        self.current_step = 0
        
        # Internal state
        self.green_times = np.full(self.num_junctions, self.base_green_time)
        
        # Initial queues scaled by total incidents and junction risk
        self.queues = np.zeros(self.num_junctions)
        for i, j in enumerate(self.junctions):
            self.queues[i] = (self.total_incidents * 0.5) * j.get('risk_score', 0.5)
            
        self.crowd_remaining = 1.0
        
        return self._get_obs(), {}
        
    def _get_obs(self):
        obs = np.zeros(23, dtype=np.float32)
        
        # 0-4: Green times (normalized 0 to 120s)
        obs[0:5] = self.green_times / 120.0
        
        # 5-9: Queues (normalized ~0 to 1000)
        obs[5:10] = np.clip(self.queues / 1000.0, 0.0, 1.0)
        
        # 10-14: Centrality
        for i, j in enumerate(self.junctions):
            obs[10+i] = float(j.get('centrality', 0.05))
            
        # 15: Crowd
        obs[15] = self.crowd_remaining
        
        # 16-17: Time of day
        curr_hour = self.start_hour + (self.current_step / 60.0)
        obs[16] = math.sin(2 * math.pi * curr_hour / 24.0)
        obs[17] = math.cos(2 * math.pi * curr_hour / 24.0)
        
        # 18: Rain
        obs[18] = 1.0 if self.rain else 0.0
        
        # 19-22: Event type one hot
        types = ["protest", "public_event", "sports", "vip_movement"]
        idx = types.index(self.event_type) if self.event_type in types else 1
        obs[19 + idx] = 1.0
        
        return obs
        
    def step(self, action):
        self.current_step += 1
        
        # Actions: [0, 1, 2] -> [-5s, 0s, +5s]
        adjustments = (np.array(action) - 1) * 5.0
        
        # Apply adjustments
        self.green_times += adjustments
        
        # Safety clipping: min 10s, max 90s green time
        violations = 0
        for i in range(self.num_junctions):
            if self.green_times[i] < 10.0:
                self.green_times[i] = 10.0
                violations += 1
            elif self.green_times[i] > 90.0:
                self.green_times[i] = 90.0
                violations += 1
                
        # Simulate traffic flow
        # Arrival rate depends on crowd remaining and total incidents
        # Crowd decays exponentially
        tau = 30.0 # 30 mins to flush ~63%
        prev_crowd = self.crowd_remaining
        self.crowd_remaining = math.exp(-self.current_step / tau)
        
        arriving_crowd_pct = prev_crowd - self.crowd_remaining
        total_arrivals = arriving_crowd_pct * self.total_incidents * 3.0 # multiplier for scale
        
        for i, j in enumerate(self.junctions):
            # Arrivals proportional to risk score
            arrivals = total_arrivals * j.get('risk_score', 0.5)
            
            # Service rate (vehicles cleared per minute) depends on green time
            # Assume cycle length ~100s. Green ratio = green / 100
            # Assume max flow rate = 40 vehicles / minute of pure green
            green_ratio = self.green_times[i] / 100.0
            cleared = green_ratio * 40.0 * (0.7 if self.rain else 1.0)
            
            self.queues[i] = max(0.0, self.queues[i] + arrivals - cleared)
            
        # Compute Reward
        avg_queue = np.mean(self.queues)
        
        # Penalties
        alpha = 1.0 # Queue penalty
        beta = 0.5  # Evacuation time penalty
        gamma = 5.0 # Safety violation penalty
        
        reward = - (alpha * (avg_queue / 100.0)) - beta - (gamma * violations)
        
        # Bonus for clearing traffic
        if avg_queue < 20.0:
            reward += 2.0
            
        done = self.current_step >= self.max_steps or self.crowd_remaining < 0.05
        
        return self._get_obs(), float(reward), bool(done), False, {"avg_queue": avg_queue, "violations": violations}
