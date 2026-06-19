import pytest
from rl.gym_env import EventFlowEnv
import numpy as np

def test_env_initialization():
    env = EventFlowEnv(G=None)
    obs, info = env.reset()
    
    assert env.observation_space.shape == (23,)
    assert obs.shape == (23,)
    assert env.action_space.nvec.tolist() == [3, 3, 3, 3, 3]
    
def test_env_step():
    env = EventFlowEnv(G=None)
    env.reset()
    
    # take neutral action
    obs, reward, done, _, info = env.step([1, 1, 1, 1, 1])
    
    assert isinstance(reward, float)
    assert isinstance(done, bool)
    assert 'avg_queue' in info
    assert obs.shape == (23,)

def test_env_action_bounds():
    env = EventFlowEnv(G=None)
    env.reset()
    
    # Green times should not exceed 90s or drop below 10s
    for _ in range(20):
        env.step([2, 2, 2, 2, 2]) # max extension
        
    for g in env.green_times:
        assert g <= 90.0
        
    for _ in range(30):
        env.step([0, 0, 0, 0, 0]) # max reduction
        
    for g in env.green_times:
        assert g >= 10.0
