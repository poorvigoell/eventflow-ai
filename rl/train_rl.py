"""
Single-agent RL training script (legacy).
For the newer Multi-Agent RL (MARL) cooperative model, see: rl/train_marl.py
"""

import os
import argparse
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback

from rl.gym_env import EventFlowEnv

def train(timesteps=100000):
    print("Setting up EventFlow environment...")
    # Passing G=None to use synthetic junctions for much faster training
    env = EventFlowEnv(G=None)
    
    print("Initializing PPO agent...")
    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log="./rl/logs/")
    
    os.makedirs("./rl/checkpoints", exist_ok=True)
    checkpoint_callback = CheckpointCallback(save_freq=20000, save_path='./rl/checkpoints/', name_prefix='ppo_eventflow')
    
    print(f"Starting training for {timesteps} timesteps...")
    model.learn(total_timesteps=timesteps, callback=checkpoint_callback)
    
    final_path = "./rl/checkpoints/ppo_eventflow.zip"
    model.save(final_path)
    print(f"Training complete. Model saved to {final_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--timesteps', type=int, default=100000)
    args = parser.parse_args()
    train(args.timesteps)
