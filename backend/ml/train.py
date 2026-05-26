"""
train.py (v5.0.0)

Trains the Patient Triage Random Forest model.

Key design decision:
    Uses the structured 83-dim binary feature vector defined in constants.FEATURE_ORDER
    instead of TF-IDF on a text blob. This preserves all clinical scoring logic
    that constants.py encodes (ESI weights, age-adjusted vitals, interactions, etc.)
    and makes the model's decisions interpretable and auditable.

Expects data/data.csv to exist. Run data_generator.py first.

Outputs:
    models/triage_pipeline.pkl   — trained sklearn Pipeline
    models/feature_names.pkl     — ordered feature name list (for predict.py)
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
import joblib

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

from constants import (
    MODEL_CONFIG,
    EXPERIMENT_VERSION,
    FEATURE_ORDER,
    KNOWN_DURATIONS,
    KNOWN_MODIFIERS,
    validate_constants,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR  = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent / "data" / "data.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
PIPELINE_PATH      = MODEL_DIR / "triage_pipeline.pkl"
FEATURE_NAMES_PATH = MODEL_DIR / "feature_names.pkl"


# ---------------------------------------------------------------------------
# Feature builder
# ---------------------------------------------------------------------------

def build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert raw CSV rows into the structured 83-dim binary feature matrix
    defined by constants.FEATURE_ORDER.

    Expected CSV columns (produced by data_generator.py):
        - One binary column per entry in FEATURE_ORDER  (0 or 1)
        - 'age'              — integer, patient age in years
        - 'duration'         — one of KNOWN_DURATIONS
        - 'patient_modifier' — one of KNOWN_MODIFIERS
        - 'department'       — target label
        - 'esi_level'        — integer 1–5 (kept for optional use, not a feature)

    All FEATURE_ORDER columns are already binary (0/1) from the generator,
    so no TF-IDF or text encoding is needed.
    The only continuous feature is 'age'; 'duration' and 'patient_modifier'
    are one-hot encoded via the ColumnTransformer in the pipeline.
    """
    # Verify every expected feature column is present
    missing = [f for f in FEATURE_ORDER if f not in df.columns]
    if missing:
        print(f"[FATAL] {len(missing)} feature column(s) missing from CSV.")
        print(f"        First 5 missing: {missing[:5]}")
        print("        Re-run data_generator.py to regenerate the dataset.")
        sys.exit(1)

    binary_cols   = FEATURE_ORDER                     # 83 binary flags
    numeric_cols  = ["age"]                           # 1 continuous feature
    cat_cols      = ["duration", "patient_modifier"]  # 2 categorical features

    all_feature_cols = binary_cols + numeric_cols + cat_cols
    return df[all_feature_cols].copy(), all_feature_cols


# ---------------------------------------------------------------------------
# Main training function
# ---------------------------------------------------------------------------

def train_model():
    print(f"\n{'='*60}")
    print(f"  Patient Triage ML Training Pipeline  |  v{EXPERIMENT_VERSION}")
    print(f"{'='*60}\n")

    # 0. Validate constants before doing anything else
    issues = validate_constants()
    if issues:
        print("[WARNING] constants.py has validation issues:")
        for w in issues:
            print(f"   ⚠  {w}")
        print()

    # 1. Load data
    if not DATA_PATH.exists():
        print(f"[FATAL] Data not found at:\n        {DATA_PATH}")
        print("        Run data_generator.py first.")
        sys.exit(1)

    df = pd.read_csv(DATA_PATH)
    print(f"[INFO] Loaded {len(df):,} patient records from {DATA_PATH.name}")

    # Sanity check target column
    if "department" not in df.columns:
        print("[FATAL] 'department' column not found in CSV. Check data_generator.py output.")
        sys.exit(1)

    # 2. Build feature matrix
    print("[INFO] Building structured feature matrix from FEATURE_ORDER...")
    X_df, all_feature_cols = build_feature_matrix(df)
    y = df["department"]

    print(f"[INFO] Feature matrix shape: {X_df.shape}")
    print(f"[INFO] Target classes ({y.nunique()}): {sorted(y.unique())}\n")

    # Class distribution
    dist = y.value_counts(normalize=True).sort_index()
    print("[INFO] Department distribution (target):")
    for dept, pct in dist.items():
        bar = "█" * int(pct * 40)
        print(f"  {dept:<25} {pct:5.1%}  {bar}")
    print()

    # 3. Train / test split  (stratified to preserve class distribution)
    X_train, X_test, y_train, y_test = train_test_split(
        X_df, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )
    print(f"[INFO] Train: {len(X_train):,} samples  |  Test: {len(X_test):,} samples\n")

    # 4. Preprocessing pipeline
    #    - Binary FEATURE_ORDER columns: already 0/1, pass through unchanged
    #    - age: StandardScaler (only continuous feature)
    #    - duration, patient_modifier: OneHotEncoder
    binary_cols  = FEATURE_ORDER
    numeric_cols = ["age"]
    cat_cols     = ["duration", "patient_modifier"]

    from sklearn.preprocessing import OneHotEncoder
    from sklearn.pipeline import Pipeline as SkPipeline

    preprocessor = ColumnTransformer(
        transformers=[
            ("binary",   "passthrough",                                    binary_cols),
            ("numeric",  StandardScaler(),                                 numeric_cols),
            ("category", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )

    # 5. Full pipeline
    classifier = RandomForestClassifier(**MODEL_CONFIG)

    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier",   classifier),
    ])

    # 6. Cross-validation on training set (5-fold stratified)
    print("[INFO] Running 5-fold stratified cross-validation on training set...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="f1_weighted", n_jobs=-1)
    print(f"[INFO] CV F1 (weighted): {cv_scores.mean():.4f}  ±  {cv_scores.std():.4f}\n")

    # 7. Final fit on full training set
    print("[INFO] Fitting final model on full training set...")
    pipeline.fit(X_train, y_train)

    # 8. Evaluation on held-out test set
    print("\n" + "="*60)
    print("  Test Set Evaluation")
    print("="*60)
    y_pred = pipeline.predict(X_test)
    print(classification_report(y_test, y_pred, zero_division=0))

    # Confusion matrix summary (only show off-diagonal misclassifications)
    cm = confusion_matrix(y_test, y_pred, labels=pipeline.classes_)
    cm_df = pd.DataFrame(cm, index=pipeline.classes_, columns=pipeline.classes_)
    misclassified = int((y_pred != y_test).sum())
    accuracy = 1 - misclassified / len(y_test)
    print(f"[INFO] Overall accuracy:    {accuracy:.4f}")
    print(f"[INFO] Misclassified cases: {misclassified} / {len(y_test)}")

    # 9. Feature importance (top 20 most predictive features)
    rf = pipeline.named_steps["classifier"]
    try:
        feature_names_out = pipeline.named_steps["preprocessor"].get_feature_names_out()
        importances = rf.feature_importances_
        top_idx = np.argsort(importances)[::-1][:20]
        print("\n[INFO] Top 20 feature importances:")
        for rank, idx in enumerate(top_idx, 1):
            name = feature_names_out[idx]
            imp  = importances[idx]
            bar  = "█" * int(imp * 400)
            print(f"  {rank:>2}. {name:<35} {imp:.4f}  {bar}")
    except Exception as e:
        print(f"[WARNING] Could not extract feature importances: {e}")

    # 10. Save artifacts
    joblib.dump(pipeline, PIPELINE_PATH)
    joblib.dump(list(all_feature_cols), FEATURE_NAMES_PATH)

    print(f"\n{'='*60}")
    print(f"[SUCCESS] Pipeline saved to:       {PIPELINE_PATH}")
    print(f"[SUCCESS] Feature names saved to:  {FEATURE_NAMES_PATH}")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    train_model()