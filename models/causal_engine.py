import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

MODEL_PATH = "models/saved/causal_model.joblib"
PREPROCESSOR_PATH = "models/saved/causal_preprocessor.joblib"

def train_causal_model(csv_path="data/causal_augmented_dataset.csv"):
    df = pd.read_csv(csv_path)
    
    # Feature extraction
    df['start_datetime'] = pd.to_datetime(df['start_datetime'])
    df['hour'] = df['start_datetime'].dt.hour
    
    # Fill missing
    df['priority'] = df['priority'].fillna('Medium')
    df['event_cause'] = df['event_cause'].fillna('other')
    
    # Define variables
    Y = df['clearance_time'].values
    T = df['barricades_deployed'].values
    
    # Confounders / Features
    categorical_features = ['priority', 'event_cause']
    numerical_features = ['hour', 'latitude', 'longitude']
    
    # Fill missing coordinates with Bangalore center
    df['latitude'] = df.get('latitude', pd.Series([12.9716]*len(df))).fillna(12.9716)
    df['longitude'] = df.get('longitude', pd.Series([77.5946]*len(df))).fillna(77.5946)
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])
    
    X_raw = df[['priority', 'event_cause', 'hour', 'latitude', 'longitude']]
    X_processed = preprocessor.fit_transform(X_raw)
    
    print("Training Custom T-Learner Causal Model...")
    X0, Y0 = X_processed[T == 0], Y[T == 0]
    X1, Y1 = X_processed[T == 1], Y[T == 1]
    
    model0 = GradientBoostingRegressor(loss='huber', n_estimators=100, random_state=42)
    model1 = GradientBoostingRegressor(loss='huber', n_estimators=100, random_state=42)
    
    model0.fit(X0, Y0)
    model1.fit(X1, Y1)
    
    # Calculate Average Treatment Effect (ATE) to verify model learned correctly
    effect = model1.predict(X_processed) - model0.predict(X_processed)
    ate = np.mean(effect)
    print(f"Average Treatment Effect (ATE): {ate:.2f} minutes")
    
    # Save the models as a dict
    est_dict = {"model0": model0, "model1": model1}
    os.makedirs("models/saved", exist_ok=True)
    joblib.dump(est_dict, MODEL_PATH)
    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    print("Causal Model and Preprocessor saved successfully.")

def predict_causal_effect(event_data):
    """
    Predicts the Individual Treatment Effect (ITE) for a specific event.
    event_data: dict with 'priority', 'event_cause', 'hour', 'latitude', 'longitude'
    Returns: float (estimated minutes saved by deploying barricades)
    """
    try:
        est_dict = joblib.load(MODEL_PATH)
        preprocessor = joblib.load(PREPROCESSOR_PATH)
    except FileNotFoundError:
        print("Model files not found. Please run train_causal_model() first.")
        return 0.0

    df = pd.DataFrame([event_data])
    
    # Ensure all required columns are present
    if 'hour' not in df.columns and 'start_datetime' in df.columns:
        df['start_datetime'] = pd.to_datetime(df['start_datetime'])
        df['hour'] = df['start_datetime'].dt.hour
        
    df['latitude'] = df.get('latitude', pd.Series([12.9716]*len(df))).fillna(12.9716)
    df['longitude'] = df.get('longitude', pd.Series([77.5946]*len(df))).fillna(77.5946)
        
    X_processed = preprocessor.transform(df)
    
    # The effect is Y(T=1) - Y(T=0)
    # A negative value means barricades REDUCE clearance time (which is good).
    model0 = est_dict["model0"]
    model1 = est_dict["model1"]
    
    ite = model1.predict(X_processed)[0] - model0.predict(X_processed)[0]
    
    return ite

if __name__ == "__main__":
    train_causal_model()
