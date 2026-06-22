"""
Training script for the MARL cooperative traffic signal model.

Uses Independent PPO with Parameter Sharing:
    - A single PPO model with a shared feature extractor
    - The feature extractor processes each agent's observation independently
    - A separate MessageNetwork generates communication vectors
    - Messages are injected into agent observations at each step

Usage:
    python -m rl.train_marl --timesteps 150000
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
import argparse
import numpy as np
import torch

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback, BaseCallback

from rl.marl_env import MARLTrafficEnv, NUM_AGENTS, OBS_DIM_PER_AGENT, MESSAGE_DIM
from rl.marl_network import MARLFeaturesExtractor, MARLMessageModule


class MessagePassingCallback(BaseCallback):
    """
    SB3 callback that runs message-passing after each step.
    
    After the PPO model collects a rollout step, this callback:
    1. Extracts the current observation from the environment
    2. Runs the MessageNetwork to produce per-agent messages
    3. Injects those messages into the environment's message buffer
    
    This creates the communication loop: agents' messages from step t
    appear in other agents' observations at step t+1.
    """

    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.message_module = None

    def _on_training_start(self):
        # Initialize the message module with the policy's feature extractor
        features_extractor = self.model.policy.features_extractor
        device = self.model.device
        self.message_module = MARLMessageModule(features_extractor, device=device)

    def _on_step(self) -> bool:
        if self.message_module is None:
            return True

        # Get current observation from the environment
        env = self.training_env.envs[0]  # VecEnv wraps it
        
        try:
            # Get the raw unwrapped MARL env
            marl_env = env
            while hasattr(marl_env, 'env'):
                marl_env = marl_env.env
            
            if hasattr(marl_env, 'set_messages'):
                obs = marl_env._get_flat_obs()
                messages = self.message_module.generate_messages(obs)
                marl_env.set_messages(messages)
        except Exception:
            pass  # Silently skip if env structure doesn't match

        return True


def train(timesteps=150000):
    print("=" * 60)
    print("  MARL Cooperative Traffic Signals — Training")
    print("=" * 60)
    
    print("\n🔧 Setting up MARL environment (synthetic junctions)...")
    env = MARLTrafficEnv(G=None, training_mode=True)

    print("🧠 Initializing PPO with shared MARL feature extractor...")
    
    policy_kwargs = {
        "features_extractor_class": MARLFeaturesExtractor,
        "features_extractor_kwargs": {"features_dim": 128},
        "net_arch": dict(pi=[256, 128], vf=[256, 128]),
    }
    
    model = PPO(
        "MlpPolicy",
        env,
        policy_kwargs=policy_kwargs,
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
    )

    os.makedirs("./rl/checkpoints", exist_ok=True)
    
    checkpoint_cb = CheckpointCallback(
        save_freq=25000,
        save_path='./rl/checkpoints/',
        name_prefix='ppo_marl_eventflow',
    )
    message_cb = MessagePassingCallback()

    print(f"\n🚀 Starting training for {timesteps:,} timesteps...")
    print(f"   Agents: {NUM_AGENTS}")
    print(f"   Obs dim per agent: {OBS_DIM_PER_AGENT}")
    print(f"   Message dim: {MESSAGE_DIM}")
    print(f"   Action choices: 5 ([-10, -5, 0, +5, +10] sec)")
    print()

    print("BEFORE LEARN")
    model.learn(
        total_timesteps=timesteps,
        callback=[checkpoint_cb, message_cb],
    )
    print("AFTER LEARN")

    final_path = "./rl/checkpoints/ppo_marl_eventflow.zip"
    model.save(final_path)
    
    # Save the message network weights separately
    if message_cb.message_module is not None:
        msg_path = "./rl/checkpoints/marl_message_net.pt"
        torch.save(message_cb.message_module.state_dict(), msg_path)
        print(f"💬 Message network saved to {msg_path}")
    
    print(f"\n✅ Training complete! Model saved to {final_path}")
    print(f"   Total params: {sum(p.numel() for p in model.policy.parameters()):,}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train MARL cooperative traffic model")
    parser.add_argument('--timesteps', type=int, default=150000,
                        help='Total training timesteps (default: 150000)')
    args = parser.parse_args()
    train(args.timesteps)
