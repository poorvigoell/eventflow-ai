import pandas as pd
import numpy as np
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.geo import haversine_distance
from data.loader import load_and_clean_data, split_planned_unplanned

RADIUS_KM = 2.0
TIME_WINDOW_HOURS = 3.0

def correlate_events(planned_df, unplanned_df):
    training_rows = []

    for idx, event in planned_df.iterrows():
        event_lat = event['latitude']
        event_lng = event['longitude']
        event_start = event['start_datetime']
        event_end = event['end_datetime']
        event_duration = event['duration_hours']

        inflow_start = event_start - pd.Timedelta(hours=TIME_WINDOW_HOURS)
        inflow_end = event_start
        steady_start = event_start
        steady_end = event_end
        exodus_start = event_end
        exodus_end = event_end + pd.Timedelta(hours=TIME_WINDOW_HOURS)

        nearby_mask = unplanned_df.apply(
            lambda row: haversine_distance(event_lat, event_lng, row['latitude'], row['longitude']) <= RADIUS_KM,
            axis=1
        )
        nearby_incidents = unplanned_df[nearby_mask]

        inflow_count = 0
        steady_count = 0
        exodus_count = 0

        for _, inc in nearby_incidents.iterrows():
            inc_time = inc['start_datetime']
            if inflow_start <= inc_time < inflow_end:
                inflow_count += 1
            elif steady_start <= inc_time < steady_end:
                steady_count += 1
            elif exodus_start <= inc_time <= exodus_end:
                exodus_count += 1

        total_incidents = inflow_count + steady_count + exodus_count

        training_rows.append({
            'event_id': event['id'],
            'event_cause': event['event_cause'],
            'latitude': event_lat,
            'longitude': event_lng,
            'zone': event['zone'],
            'hour': event_start.hour,
            'day_of_week': event_start.dayofweek,
            'duration_hours': event_duration,
            'priority': event['priority'],
            'inflow_incidents': inflow_count,
            'steady_incidents': steady_count,
            'exodus_incidents': exodus_count,
            'total_incidents': total_incidents,
        })

        if (len(training_rows) % 50) == 0:
            print(f"  Processed {len(training_rows)}/{len(planned_df)} planned events...")

    training_df = pd.DataFrame(training_rows)
    return training_df

if __name__ == "__main__":
    csv_path = r"C:\Users\poorv\Downloads\Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
    df = load_and_clean_data(csv_path)
    if df is None:
        sys.exit(1)

    planned, unplanned = split_planned_unplanned(df)
    print(f"\nCorrelating {len(planned)} planned events against {len(unplanned)} unplanned incidents...")
    print(f"  Radius: {RADIUS_KM} km | Time Window: ±{TIME_WINDOW_HOURS} hrs")

    training_df = correlate_events(planned, unplanned)

    processed_dir = os.path.join(os.path.dirname(__file__), 'processed')
    os.makedirs(processed_dir, exist_ok=True)
    out_path = os.path.join(processed_dir, 'training_data.pkl')
    training_df.to_pickle(out_path)

    print(f"\nTraining DataFrame saved to {out_path}")
    print(f"Shape: {training_df.shape}")
    print(f"\nIncident Stats:")
    print(f"  Events with 0 nearby incidents: {(training_df['total_incidents'] == 0).sum()}")
    print(f"  Max incidents near a single event: {training_df['total_incidents'].max()}")
    print(f"  Mean incidents per event: {training_df['total_incidents'].mean():.2f}")
    print(f"\nPhase Breakdown (mean per event):")
    print(f"  Inflow:  {training_df['inflow_incidents'].mean():.2f}")
    print(f"  Steady:  {training_df['steady_incidents'].mean():.2f}")
    print(f"  Exodus:  {training_df['exodus_incidents'].mean():.2f}")
