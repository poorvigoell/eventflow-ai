import os
import json
import numpy as np
from stable_baselines3 import PPO
from rl.gym_env import EventFlowEnv
from utils.traffic_signals import calculate_webster_timing

def run_rl_agent(env, model, episodes=5):
    rewards = []
    queue_pcts = []
    for _ in range(episodes):
        obs, _ = env.reset()
        done = False
        ep_reward = 0
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, _, info = env.step(action)
            ep_reward += reward
        rewards.append(ep_reward)
        queue_pcts.append(info['avg_queue'])
    return {"mean_reward": float(np.mean(rewards)), "final_avg_queue": float(np.mean(queue_pcts))}

def run_random_agent(env, episodes=5):
    rewards = []
    queue_pcts = []
    for _ in range(episodes):
        obs, _ = env.reset()
        done = False
        ep_reward = 0
        while not done:
            action = env.action_space.sample()
            obs, reward, done, _, info = env.step(action)
            ep_reward += reward
        rewards.append(ep_reward)
        queue_pcts.append(info['avg_queue'])
    return {"mean_reward": float(np.mean(rewards)), "final_avg_queue": float(np.mean(queue_pcts))}

def run_webster_baseline(env, episodes=5):
    # Webster formula keeps fixed timing based on initial flow ratios
    rewards = []
    queue_pcts = []
    for _ in range(episodes):
        obs, _ = env.reset()
        # initial state to calculate flows
        flows = []
        for j in env.junctions:
            flows.append(j.get('risk_score', 0.5) * 0.5)
        # normalize
        total = sum(flows)
        if total > 0:
            flows = [f/total for f in flows]
        else:
            flows = [0.2] * 5
            
        # calculate webster fixed green times
        timing = calculate_webster_timing(flows)
        # map phases to green times, cap to 10-90s
        fixed_greens = []
        for i in range(env.num_junctions):
            if i < len(timing['phases']):
                g = timing['phases'][i]['green_sec']
            else:
                g = 45.0
            fixed_greens.append(max(10.0, min(90.0, g)))
            
        done = False
        ep_reward = 0
        while not done:
            # Action: determine required adjustment to reach fixed_green
            action = []
            for i in range(env.num_junctions):
                diff = fixed_greens[i] - env.green_times[i]
                if diff > 2.5:
                    action.append(2) # +5
                elif diff < -2.5:
                    action.append(0) # -5
                else:
                    action.append(1) # 0
            
            obs, reward, done, _, info = env.step(action)
            ep_reward += reward
        rewards.append(ep_reward)
        queue_pcts.append(info['avg_queue'])
    return {"mean_reward": float(np.mean(rewards)), "final_avg_queue": float(np.mean(queue_pcts))}

if __name__ == "__main__":
    env = EventFlowEnv(G=None)
    model_path = "./rl/checkpoints/ppo_eventflow.zip"
    
    if os.path.exists(model_path):
        model = PPO.load(model_path, env=env)
        print("Running RL Agent...")
        rl_res = run_rl_agent(env, model)
    else:
        rl_res = {"error": "No model found"}
        
    print("Running Random Agent...")
    rand_res = run_random_agent(env)
    
    print("Running Webster Baseline...")
    webster_res = run_webster_baseline(env)
    
    # --- MARL Evaluation ---
    marl_res = {"error": "No MARL model found"}
    marl_model_path = "./rl/checkpoints/ppo_marl_eventflow.zip"
    if os.path.exists(marl_model_path):
        try:
            from rl.marl_env import MARLTrafficEnv
            from rl.marl_network import MARLFeaturesExtractor
            
            print("Running MARL Cooperative Agent...")
            marl_env = MARLTrafficEnv(G=None)
            policy_kwargs = {
                "features_extractor_class": MARLFeaturesExtractor,
                "features_extractor_kwargs": {"features_dim": 128},
            }
            marl_model = PPO.load(marl_model_path, env=marl_env)
            
            marl_rewards = []
            marl_queues = []
            for _ in range(5):
                obs, _ = marl_env.reset()
                done = False
                ep_reward = 0
                while not done:
                    action, _ = marl_model.predict(obs, deterministic=True)
                    obs, reward, done, _, info = marl_env.step(action)
                    ep_reward += reward
                marl_rewards.append(ep_reward)
                marl_queues.append(info['avg_queue'])
            
            marl_res = {
                "mean_reward": float(np.mean(marl_rewards)),
                "final_avg_queue": float(np.mean(marl_queues)),
                "per_agent_queues": info.get('per_agent_queues', []),
            }
        except Exception as e:
            marl_res = {"error": str(e)}
    
    report = {
        "rl_agent": rl_res,
        "marl_cooperative_agent": marl_res,
        "random_agent": rand_res,
        "webster_baseline": webster_res
    }
    
    os.makedirs("./rl/reports", exist_ok=True)
    with open("./rl/reports/evaluation.json", "w") as f:
        json.dump(report, f, indent=4)
        
    print(json.dumps(report, indent=4))
