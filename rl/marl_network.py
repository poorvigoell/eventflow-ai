"""
Custom MARL Policy Network for stable-baselines3 PPO.

Architecture:
    Input (OBS_DIM_PER_AGENT per agent) 
        → SharedMLP(128, 128) 
        → ActionHead (ACTION_CHOICES outputs, categorical)
        → MessageHead (MESSAGE_DIM outputs, tanh)

Parameter sharing: the same network weights are used for all agents.
The wrapper splits the flattened observation, runs the network N times,
and reassembles the outputs.
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Tuple, Type

from stable_baselines3.common.policies import ActorCriticPolicy
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from gymnasium import spaces


# ---------------------------------------------------------------------------
# Constants (must match marl_env.py)
# ---------------------------------------------------------------------------
NUM_AGENTS = 5
MESSAGE_DIM = 4
OBS_DIM_PER_AGENT = 15
ACTION_CHOICES = 5


class MARLFeaturesExtractor(BaseFeaturesExtractor):
    """
    Custom feature extractor that processes the flattened multi-agent
    observation. It splits the flat vector into per-agent chunks, runs a
    shared MLP on each, and concatenates the results.
    
    This ensures parameter sharing across agents while maintaining
    individual observations.
    """

    def __init__(self, observation_space: spaces.Box, features_dim: int = 128):
        # SB3 expects features_dim to be the final output dim
        super().__init__(observation_space, features_dim * NUM_AGENTS)
        
        self.agent_obs_dim = OBS_DIM_PER_AGENT
        self.per_agent_features_dim = features_dim

        # Shared encoder applied to each agent's observation
        self.shared_encoder = nn.Sequential(
            nn.Linear(self.agent_obs_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, features_dim),
            nn.ReLU(),
        )

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        batch_size = observations.shape[0]
        
        # Split into per-agent observations
        agent_obs_list = []
        for i in range(NUM_AGENTS):
            start = i * self.agent_obs_dim
            end = start + self.agent_obs_dim
            agent_obs_list.append(observations[:, start:end])
        
        # Run shared encoder on each agent
        agent_features = []
        for agent_obs in agent_obs_list:
            features = self.shared_encoder(agent_obs)
            agent_features.append(features)
        
        # Concatenate all agent features
        return torch.cat(agent_features, dim=1)


class MessageNetwork(nn.Module):
    """
    Standalone message-generation network.
    Takes the per-agent features and produces a MESSAGE_DIM vector
    for inter-agent communication.
    
    Output is tanh-activated so values are in [-1, 1].
    """

    def __init__(self, input_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, MESSAGE_DIM),
            nn.Tanh(),
        )

    def forward(self, agent_features: torch.Tensor) -> torch.Tensor:
        """
        agent_features: (batch_size, per_agent_features_dim)
        Returns: (batch_size, MESSAGE_DIM)
        """
        return self.net(agent_features)


class MARLMessageModule:
    """
    Utility class that wraps the MessageNetwork for use during inference.
    
    Usage:
        module = MARLMessageModule(features_extractor)
        messages = module.generate_messages(obs_tensor)
        env.set_messages(messages)
    """

    def __init__(self, features_extractor: MARLFeaturesExtractor, device="cpu"):
        self.features_extractor = features_extractor
        self.device = device
        self.per_agent_dim = features_extractor.per_agent_features_dim
        
        # One message network (shared across agents via parameter sharing)
        self.message_net = MessageNetwork(input_dim=self.per_agent_dim).to(device)

    def generate_messages(self, flat_obs: np.ndarray) -> np.ndarray:
        """
        Given a flat observation vector (from env), produce message vectors
        for all agents.
        
        flat_obs: shape (NUM_AGENTS * OBS_DIM_PER_AGENT,) or (1, ...)
        Returns: shape (NUM_AGENTS, MESSAGE_DIM)
        """
        with torch.no_grad():
            obs_tensor = torch.FloatTensor(flat_obs).to(self.device)
            if obs_tensor.dim() == 1:
                obs_tensor = obs_tensor.unsqueeze(0)

            # Extract per-agent features using the shared encoder
            batch_size = obs_tensor.shape[0]
            messages = np.zeros((NUM_AGENTS, MESSAGE_DIM), dtype=np.float32)

            for i in range(NUM_AGENTS):
                start = i * OBS_DIM_PER_AGENT
                end = start + OBS_DIM_PER_AGENT
                agent_obs = obs_tensor[:, start:end]
                agent_feat = self.features_extractor.shared_encoder(agent_obs)
                msg = self.message_net(agent_feat)
                messages[i] = msg[0].cpu().numpy()

        return messages

    def state_dict(self):
        return self.message_net.state_dict()

    def load_state_dict(self, state_dict):
        self.message_net.load_state_dict(state_dict)
