@echo off
setlocal

:: 1. Verify Python Version
echo Checking Python version...
set PYTHON_CMD=
for %%P in (python py python3.12 python3.11) do (
    %%P -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) and sys.version_info < (3, 13) else 1)" 2>NUL
    if not errorlevel 1 (
        set PYTHON_CMD=%%P
        goto :found_python
    )
)

:found_python
if "%PYTHON_CMD%"=="" (
    echo Warning: Could not find Python 3.11 or 3.12.
    echo This project requires Python 3.11 or 3.12 because PyTorch/stable-baselines3 do not yet support Python 3.13.
    echo Please install Python 3.12 and try again.
    exit /b 1
)

echo Found compatible Python: %PYTHON_CMD%

:: 2. Create and activate virtual environment
echo Creating virtual environment (.venv)...
%PYTHON_CMD% -m venv .venv
call .venv\Scripts\activate.bat

:: 3. Install dependencies
echo Installing requirements (this may take a few minutes)...
python -m pip install --upgrade pip
pip install -r requirements.txt

:: 4. Generate Causal CSV
echo Generating synthetic causal dataset locally...
python scripts\augment_causal_data.py

:: 5. Retrain Causal Model
echo Retraining Causal Model to sync with local scikit-learn version...
python models\causal_engine.py

:: 6. Train Reinforcement Learning Models
if not exist "models\rl_model.zip" if not exist "rl\checkpoints\ppo_eventflow.zip" (
    echo Training Baseline RL Agent (this takes a few seconds)...
    python -m rl.train_rl
) else (
    echo Baseline RL Agent already exists. Skipping training.
)

if not exist "rl\checkpoints\ppo_marl_eventflow.zip" (
    echo Training Cooperative MARL Agents (this takes a bit longer)...
    set PYTHONPATH=.
    python rl\train_marl.py
) else (
    echo Cooperative MARL Agents already exist. Skipping training.
)

echo Setup Complete!
echo.
echo To start the backend, run:
echo call .venv\Scripts\activate.bat
echo set OMP_NUM_THREADS=1
echo python -m uvicorn api.main:app --reload --port 8000
