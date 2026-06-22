#!/bin/bash
# EventFlow Auto-Setup Script
# This script ensures the project runs smoothly for all users by isolating dependencies
# and synchronizing the ML models with the local scikit-learn version.

echo "Starting EventFlow Setup..."

# 1. Check Python version
PYTHON_CMD="python3"
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
else
    echo "Warning: Could not find Python 3.11 or 3.12."
    echo "This project requires Python 3.11 or 3.12 because PyTorch/stable-baselines3 do not yet support Python 3.13."
    echo "Attempting to continue with $PYTHON_CMD, but installation may fail..."
fi

# 2. Create and activate virtual environment
echo "Creating virtual environment (.venv)..."
$PYTHON_CMD -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
echo "Installing requirements (this may take a few minutes for ML libraries)..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Retrain Causal Model to prevent 'Pickle / _loss' errors across environments
echo "Retraining Causal Model to sync with local scikit-learn version..."
python models/causal_engine.py

# 5. Train Reinforcement Learning Models
if [ ! -f "models/rl_model.zip" ] && [ ! -f "rl/checkpoints/ppo_eventflow.zip" ]; then
    echo "Training Baseline RL Agent (this takes a few seconds)..."
    python -m rl.train_rl
else
    echo "Baseline RL Agent already exists. Skipping training."
fi

if [ ! -f "rl/checkpoints/ppo_marl_eventflow.zip" ]; then
    echo "Training Cooperative MARL Agents (this takes a bit longer)..."
    export PYTHONPATH=. && python rl/train_marl.py
else
    echo "Cooperative MARL Agents already exist. Skipping training."
fi

echo "Setup Complete!"
echo ""
echo "To start the backend, run:"
echo "source .venv/bin/activate && OMP_NUM_THREADS=1 python -m uvicorn api.main:app --reload --port 8000"
