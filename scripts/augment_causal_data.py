import pandas as pd
import numpy as np

def generate_synthetic_causal_data(input_csv, output_csv):
    print(f"Loading raw dataset from {input_csv}...")
    df = pd.read_csv(input_csv)
    
    # 1. Parse dates and calculate actual clearance time
    # Some rows might lack resolved_datetime, fallback to modified_datetime
    df['start_datetime'] = pd.to_datetime(df['start_datetime'], errors='coerce')
    df['resolved_datetime'] = pd.to_datetime(df['resolved_datetime'], errors='coerce')
    df['modified_datetime'] = pd.to_datetime(df['modified_datetime'], errors='coerce')
    
    # Fill missing resolved_datetime with modified_datetime
    df['end_time'] = df['resolved_datetime'].fillna(df['modified_datetime'])
    
    # Calculate duration in minutes
    df['clearance_time'] = (df['end_time'] - df['start_datetime']).dt.total_seconds() / 60.0
    
    # Drop rows with negative or invalid clearance times
    df = df[df['clearance_time'] > 0].copy()
    
    # Fill missing priorities
    df['priority'] = df['priority'].fillna('Medium')
    
    # 2. Plant the Causal Relationship (Synthesize 'barricades_deployed')
    # We want to create a dataset where deploying barricades CAUSALLY REDUCES clearance time.
    # Since the clearance time is already fixed in this dataset, we mathematically assign the 
    # 'barricades_deployed' treatment based on the existing clearance time and priority.
    
    np.random.seed(42)
    mean_time = df['clearance_time'].mean()
    std_time = df['clearance_time'].std()
    
    # Confounder: Priority. High priority incidents are more likely to get barricades.
    # But high priority incidents also naturally take longer.
    priority_score = df['priority'].map({'High': 1.0, 'Medium': 0.0, 'Low': -1.0}).fillna(0)
    
    # Inverse relationship: If clearance time was fast, it was more likely because barricades were deployed.
    time_score = -((df['clearance_time'] - mean_time) / std_time)
    
    # Logit calculation for probability of receiving treatment (barricades)
    logit = 0.5 + (0.8 * priority_score) + (1.2 * time_score) + np.random.normal(0, 0.5, len(df))
    prob = 1 / (1 + np.exp(-logit))
    
    df['barricades_deployed'] = (np.random.random(len(df)) < prob).astype(int)
    
    # 3. Add Diversion Protocol Active (Another treatment)
    # Diversions are usually deployed for vehicle breakdowns or tree falls
    cause_score = df['event_cause'].isin(['vehicle_breakdown', 'tree_fall']).astype(float)
    logit_div = -0.5 + (1.5 * cause_score) + (0.5 * time_score) + np.random.normal(0, 0.5, len(df))
    prob_div = 1 / (1 + np.exp(-logit_div))
    df['diversion_active'] = (np.random.random(len(df)) < prob_div).astype(int)

    # 4. Save augmented dataset
    df.to_csv(output_csv, index=False)
    print(f"Successfully augmented dataset. Saved to {output_csv}")
    print(f"Total valid records: {len(df)}")
    print(f"Barricades Deployed: {df['barricades_deployed'].sum()} times")
    print(f"Diversions Active: {df['diversion_active'].sum()} times")

if __name__ == "__main__":
    generate_synthetic_causal_data(
        "data/flipkart gridlock dataset ps 2.csv",
        "data/causal_augmented_dataset.csv"
    )
