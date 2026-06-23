import pandas as pd
import numpy as np
import os

def generate_synthetic_causal_data(input_path, output_csv):
    print(f"Loading dataset from {input_path}...")
    if input_path.endswith('.pkl'):
        df = pd.read_pickle(input_path)
    else:
        df = pd.read_csv(input_path)
    
    # 1. Parse dates and calculate actual clearance time
    if 'start_datetime' in df.columns:
        df['start_datetime'] = pd.to_datetime(df['start_datetime'], errors='coerce')
        df['end_time'] = pd.to_datetime(df.get('end_datetime', df.get('resolved_datetime')), errors='coerce')
        df['clearance_time'] = (df['end_time'] - df['start_datetime']).dt.total_seconds() / 60.0
    else:
        # If using training_data.pkl, generate dummy datetimes
        base_date = pd.Timestamp("2024-01-01")
        df['start_datetime'] = base_date + pd.to_timedelta(df['hour'].fillna(12), unit='h')
        df['clearance_time'] = df['duration_hours'] * 60.0
    
    if df['clearance_time'].isna().all() and 'duration_hours' in df.columns:
        df['clearance_time'] = df['duration_hours'] * 60.0
        
    # Drop rows with negative or invalid clearance times
    df = df[df['clearance_time'] > 0].copy()
    
    # Fill missing priorities
    df['priority'] = df.get('priority', pd.Series(['Medium']*len(df))).fillna('Medium')
    
    # 2. Assign Treatments (Barricades & Diversions) based on confounders
    np.random.seed(42)
    
    # Confounders affecting treatment probability
    priority_score = df['priority'].map({'High': 1.0, 'Medium': 0.0, 'Low': -1.0}).fillna(0)
    cause_score = df.get('event_cause', pd.Series(['other']*len(df))).isin(['vehicle_breakdown', 'tree_fall']).astype(float)
    
    # Probability of barricades (higher for High priority)
    logit = 0.5 + (1.2 * priority_score) + np.random.normal(0, 0.5, len(df))
    prob = 1 / (1 + np.exp(-logit))
    df['barricades_deployed'] = (np.random.random(len(df)) < prob).astype(int)
    
    # Probability of diversions (higher for breakdowns/tree falls)
    logit_div = -0.5 + (1.5 * cause_score) + (0.5 * priority_score) + np.random.normal(0, 0.5, len(df))
    prob_div = 1 / (1 + np.exp(-logit_div))
    df['diversion_active'] = (np.random.random(len(df)) < prob_div).astype(int)

    # 3. Simulate true causal effect on clearance_time
    # Cap base clearance time to a realistic value (between 30 and 180 minutes)
    df['base_clearance'] = np.clip(df['clearance_time'], 30, 180)
    
    # Define the true causal effect (ITE)
    # Barricades save ~25 mins, Diversions save ~15 mins. (Adding some noise)
    effect_barricades = -np.random.normal(25.0, 5.0, len(df)) 
    effect_diversions = -np.random.normal(15.0, 3.0, len(df))
    
    # Apply effects
    df['clearance_time'] = df['base_clearance'] + (df['barricades_deployed'] * effect_barricades) + (df['diversion_active'] * effect_diversions)
    
    # Ensure it never goes below a minimum realistic time (e.g., 10 minutes)
    df['clearance_time'] = np.clip(df['clearance_time'], 10, None)

    # 4. Save augmented dataset
    df.to_csv(output_csv, index=False)
    print(f"Successfully augmented dataset. Saved to {output_csv}")
    print(f"Total valid records: {len(df)}")
    print(f"Barricades Deployed: {df['barricades_deployed'].sum()} times")
    print(f"Diversions Active: {df['diversion_active'].sum()} times")

if __name__ == "__main__":
    generate_synthetic_causal_data(
        "data/processed/training_data.pkl",
        "data/causal_augmented_dataset.csv"
    )
