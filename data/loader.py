import pandas as pd
import numpy as np
import os
import sys

# Ensure project root is in path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.constants import ZONES, KEEP_COLUMNS

def assign_zone(lat, lng):
    if pd.isna(lat) or pd.isna(lng) or lat == 0 or lng == 0:
        return 'Unknown'
    
    for zone, bbox in ZONES.items():
        if (bbox['lat_min'] <= lat <= bbox['lat_max']) and \
           (bbox['lng_min'] <= lng <= bbox['lng_max']):
            return zone
    return 'Unknown'

def load_and_clean_data(csv_path):
    print(f"Loading data from {csv_path}...")
    try:
        df = pd.read_csv(csv_path, low_memory=False)
    except FileNotFoundError:
        print(f"Error: Could not find {csv_path}")
        return None

    # Keep only relevant columns if they exist
    cols_to_keep = [c for c in KEEP_COLUMNS if c in df.columns]
    df = df[cols_to_keep].copy()

    # Drop rows with totally missing or 0 coordinates
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df = df.dropna(subset=['latitude', 'longitude'])
    df = df[(df['latitude'] != 0) & (df['longitude'] != 0)]

    # Parse datetimes
    df['start_datetime'] = pd.to_datetime(df['start_datetime'], errors='coerce')
    df['end_datetime'] = pd.to_datetime(df['end_datetime'], errors='coerce')

    # Drop rows without a valid start time
    df = df.dropna(subset=['start_datetime'])

    # Impute missing end times (+2 hours)
    missing_end = df['end_datetime'].isna()
    df.loc[missing_end, 'end_datetime'] = df.loc[missing_end, 'start_datetime'] + pd.Timedelta(hours=2)

    # Calculate duration in hours
    df['duration_hours'] = (df['end_datetime'] - df['start_datetime']).dt.total_seconds() / 3600.0
    
    # Filter out negative durations and highly unrealistic outliers (e.g., > 48 hours)
    df = df[(df['duration_hours'] > 0) & (df['duration_hours'] <= 48)]

    # Assign fallback zones if zone column missing or null
    if 'zone' not in df.columns:
        df['zone'] = None

    missing_zone = df['zone'].isna()
    if missing_zone.any():
        df.loc[missing_zone, 'zone'] = df[missing_zone].apply(
            lambda row: assign_zone(row['latitude'], row['longitude']), axis=1
        )

    # Create processed dir if not exists
    processed_dir = os.path.join(os.path.dirname(__file__), 'processed')
    os.makedirs(processed_dir, exist_ok=True)

    # Save to pickle
    out_path = os.path.join(processed_dir, 'clean_events.pkl')
    df.to_pickle(out_path)
    print(f"Successfully cleaned {len(df)} rows. Saved to {out_path}")
    
    return df

def split_planned_unplanned(df):
    """Splits the dataframe into planned events and unplanned incidents"""
    planned_df = df[df['event_type'] == 'planned'].copy()
    unplanned_df = df[df['event_type'] == 'unplanned'].copy()
    return planned_df, unplanned_df

if __name__ == "__main__":
    csv_path = r"C:\Users\poorv\Downloads\Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
    df = load_and_clean_data(csv_path)
    if df is not None:
        planned, unplanned = split_planned_unplanned(df)
        print("\nDataframe Info:")
        print(df.info())
        print("\nSplit Info:")
        print(f"Planned Events: {len(planned)}")
        print(f"Unplanned Incidents: {len(unplanned)}")
        print("\nZone Distribution:")
        print(df['zone'].value_counts())
