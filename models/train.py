import pandas as pd
import numpy as np
import os
import sys
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

try:
    from xgboost import XGBRegressor
except ImportError:
    print("xgboost not installed. Run: pip install xgboost")
    sys.exit(1)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

FEATURE_COLS = ['event_cause', 'zone', 'hour', 'day_of_week', 'duration_hours', 'priority', 'latitude', 'longitude']
TARGET_COL = 'total_incidents'

def build_features(df):
    df = df.copy()
    df['event_cause'] = df['event_cause'].astype('category').cat.codes
    df['zone'] = df['zone'].astype('category').cat.codes
    df['priority'] = df['priority'].map({'Low': 0, 'High': 1}).fillna(0).astype(int)
    return df

def train_model(training_data_path=None):
    if training_data_path is None:
        training_data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'training_data.pkl')

    print(f"Loading training data from {training_data_path}...")
    df = pd.read_pickle(training_data_path)
    print(f"Loaded {len(df)} training samples.")

    df = build_features(df)

    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        objective='reg:squarederror'
    )

    print("Training XGBoost model...")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"\nModel Performance:")
    print(f"  MAE:  {mae:.3f}")
    print(f"  R²:   {r2:.3f}")

    importances = dict(zip(FEATURE_COLS, model.feature_importances_))
    sorted_imp = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    print(f"\nFeature Importance:")
    for feat, imp in sorted_imp:
        print(f"  {feat:20s} {imp:.4f}")

    saved_dir = os.path.join(os.path.dirname(__file__), 'saved')
    os.makedirs(saved_dir, exist_ok=True)
    model_path = os.path.join(saved_dir, 'xgb_incident_model.joblib')
    joblib.dump(model, model_path)
    print(f"\nModel saved to {model_path}")

    meta = {
        'feature_cols': FEATURE_COLS,
        'target_col': TARGET_COL,
        'mae': mae,
        'r2': r2,
        'n_train': len(X_train),
        'n_test': len(X_test),
    }
    meta_path = os.path.join(saved_dir, 'model_meta.joblib')
    joblib.dump(meta, meta_path)
    print(f"Metadata saved to {meta_path}")

    return model, meta

if __name__ == "__main__":
    train_model()
