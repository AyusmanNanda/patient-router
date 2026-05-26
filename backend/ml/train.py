import os

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer

from sklearn.compose import ColumnTransformer, make_column_transformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder

import joblib
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR.parent / "data" / "data.csv"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

def train():
    df = []
    try:
        df = pd.read_csv(DATA_DIR)
    except FileNotFoundError:
        print(f"Failed to load data.csv from {DATA_DIR}")
        exit(1)

    df["text"] = df["symptoms"] + " " + df["vitals"]

    X = df[["text", "age", "duration", "gender"]]
    y = df["department"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    text_transformer = CountVectorizer()
    categorical_transformer = OneHotEncoder(handle_unknown="ignore")
    preprocessor = make_column_transformer(
        (text_transformer, "text"),
        ("passthrough", ["age", "duration"]),
        (categorical_transformer, ["gender"]),

    )

    model = make_pipeline(preprocessor, RandomForestClassifier(n_estimators=100, random_state=42))
    model.fit(X_train, y_train)

    train_accuracy = model.score(X_train, y_train)
    test_accuracy = model.score(X_test, y_test)

    print(f"Train Accuracy: {train_accuracy * 100:.4f}%")
    print(f"Test Accuracy: {test_accuracy * 100:.4f}%")

    if train_accuracy - test_accuracy > 0.05:
        print("Warning: Possible overfitting detected")

    print(f"Department distribution: \n{df['department'].value_counts()}")

    joblib.dump(model, MODELS_DIR / "model.pkl")
    print("Model saved")

if __name__ == "__main__":
    train()







