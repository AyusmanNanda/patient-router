"""
compare_models.py

Benchmarks multiple classification algorithms on the patient-router dataset,
using the SAME preprocessing pipeline, train/test split, and edge-case suite
as train.py / model_evaluation.py, so the comparison is apples-to-apples.

Run:
    python -m ml.compare_models

Outputs:
    - printed comparison table (console)
    - ../reports/model_comparison.csv
    - ../reports/model_comparison.md   (markdown table, easy to paste into a doc)
    - ../reports/model_comparison.png  (bar chart)
"""

import time
import warnings
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.compose import make_column_transformer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import OneHotEncoder, LabelEncoder

from ml.model_evaluation import REAL_WORLD_CASES

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent
DATA_PATH   = BASE_DIR.parent / "data" / "data.csv"
REPORTS_DIR = BASE_DIR.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

TEST_SIZE    = 0.2
RANDOM_STATE = 42
CV_FOLDS     = 5


def load_data():
    try:
        df = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        print(f"[ERROR] data.csv not found at {DATA_PATH}")
        exit(1)
    df["history"] = df["history"].fillna("")
    print(df["department"].value_counts())
    before = len(df)
    df = df.dropna(subset=["department", "symptoms", "vitals", "age", "duration", "gender"])
    dropped = before - len(df)
    if dropped:
        print(f"[WARN] dropped {dropped} row(s) with missing required fields (check data.csv for corruption)")

    df["text"] = df["symptoms"] + " " + df["vitals"] + " " + df["history"]
    return df


def build_preprocessor():
    """Identical to train.py — text (symptoms+vitals+history), passthrough
    numeric (age, duration), one-hot categorical (gender)."""
    return make_column_transformer(
        (CountVectorizer(), "text"),
        ("passthrough", ["age", "duration"]),
        (OneHotEncoder(handle_unknown="ignore"), ["gender"]),
    )


def get_candidate_models():
    """Models to compare. Add/remove freely — everything downstream just
    iterates over this dict."""
    models = {
        "Decision Tree": DecisionTreeClassifier(random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE),
        "Gradient Boosting": GradientBoostingClassifier(random_state=RANDOM_STATE),
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
        "K-Nearest Neighbors": KNeighborsClassifier(n_neighbors=5),
        "SVM (RBF)": SVC(probability=True, random_state=RANDOM_STATE),
    }

    try:
        from xgboost import XGBClassifier
        models["XGBoost"] = XGBClassifier(
            n_estimators=100, random_state=RANDOM_STATE, eval_metric="mlogloss"
        )
    except ImportError:
        print("[WARN] xgboost not installed — skipping. `pip install xgboost` to include it.")

    return models


def edge_case_frame():
    rows, true = [], []
    for (sym, vit, age, dur, gen, dept, hist) in REAL_WORLD_CASES:
        text = (sym + " " + vit + " " + hist).strip()
        rows.append({"text": text, "age": age, "duration": dur, "gender": gen})
        true.append(dept)
    return pd.DataFrame(rows), true


def run_comparison():
    df = load_data()
    X = df[["text", "age", "duration", "gender"]]
    y = df["department"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    X_rw, y_rw = edge_case_frame()

    le = LabelEncoder()
    le.fit(y)  # fit once on the full label set so it's consistent everywhere

    models = get_candidate_models()
    results = []

    print(f"Training {len(models)} models on {len(X_train)} samples "
          f"({len(X_test)} held out, {len(X_rw)} edge cases)…\n")

    for name, clf in models.items():
        print(f"  → {name}")
        is_xgb = name == "XGBoost"
        pipeline = make_pipeline(build_preprocessor(), clf)

        fit_y_train = le.transform(y_train) if is_xgb else y_train

        t0 = time.time()
        pipeline.fit(X_train, fit_y_train)
        train_time = time.time() - t0

        y_pred_test = pipeline.predict(X_test)
        y_pred_rw   = pipeline.predict(X_rw)

        if is_xgb:
            y_pred_test = le.inverse_transform(y_pred_test)
            y_pred_rw   = le.inverse_transform(y_pred_rw)

        test_acc = accuracy_score(y_test, y_pred_test)
        test_f1  = f1_score(y_test, y_pred_test, average="macro", zero_division=0)
        rw_acc   = accuracy_score(y_rw, y_pred_rw)

        cv_y = le.transform(y) if is_xgb else y
        cv_scores = cross_val_score(pipeline, X, cv_y, cv=CV_FOLDS, scoring="accuracy")

        results.append({
            "Model":              name,
            "Test Accuracy (%)":  round(test_acc * 100, 2),
            "Macro F1 (%)":       round(test_f1 * 100, 2),
            "5-Fold CV (%)":      round(cv_scores.mean() * 100, 2),
            "CV Std (±%)":        round(cv_scores.std() * 100, 2),
            "Edge-Case Acc (%)":  round(rw_acc * 100, 2),
            "Generalisation Gap": round((test_acc - rw_acc) * 100, 1),
            "Train Time (s)":     round(train_time, 2),
        })

    results_df = pd.DataFrame(results).sort_values("Edge-Case Acc (%)", ascending=False)
    results_df.reset_index(drop=True, inplace=True)
    return results_df


def print_table(df):
    print("\n" + "═" * 100)
    print("  MODEL COMPARISON")
    print("═" * 100)
    print(df.to_string(index=False))
    print("═" * 100)
    best = df.iloc[0]
    print(f"\n  Best on edge cases: {best['Model']} "
          f"({best['Edge-Case Acc (%)']}% edge-case accuracy, "
          f"{best['Test Accuracy (%)']}% held-out test accuracy)\n")


def save_outputs(df):
    csv_path = REPORTS_DIR / "model_comparison.csv"
    df.to_csv(csv_path, index=False)
    print(f"  CSV saved  → {csv_path}")

    json_path = REPORTS_DIR / "model_comparison.json"
    df.to_json(json_path, orient="records", indent=4)
    print(f"  JSON saved → {json_path}")

    md_path = REPORTS_DIR / "model_comparison.md"
    try:
        table_md = df.to_markdown(index=False)
    except ImportError:
        # df.to_markdown needs the `tabulate` package; fall back to a
        # hand-rolled markdown table if it isn't installed.
        headers = list(df.columns)
        header_row = "| " + " | ".join(headers) + " |"
        sep_row    = "| " + " | ".join("---" for _ in headers) + " |"
        body_rows  = [
            "| " + " | ".join(str(v) for v in row) + " |"
            for row in df.itertuples(index=False)
        ]
        table_md = "\n".join([header_row, sep_row] + body_rows)

    with open(md_path, "w") as f:
        f.write("# Model Comparison\n\n")
        f.write(table_md)
    print(f"  MD saved   → {md_path}")

    plot_comparison(df)


def plot_comparison(df):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    plot_df = df.sort_values("Edge-Case Acc (%)")

    axes[0].barh(plot_df["Model"], plot_df["Test Accuracy (%)"],
                 color="#3b82f6", label="Held-out test", height=0.35,
                 align="edge")
    axes[0].barh(plot_df["Model"], plot_df["Edge-Case Acc (%)"],
                 color="#f97316", label="Edge cases", height=-0.35,
                 align="edge")
    axes[0].set_xlim(0, 105)
    axes[0].set_xlabel("Accuracy (%)")
    axes[0].set_title("Test vs Edge-Case Accuracy by Model")
    axes[0].legend(loc="lower right", fontsize=9)

    axes[1].barh(plot_df["Model"], plot_df["Train Time (s)"], color="#8b5cf6")
    axes[1].set_xlabel("Training time (s)")
    axes[1].set_title("Training Time by Model")

    plt.tight_layout()
    png_path = REPORTS_DIR / "model_comparison.png"
    plt.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Chart saved → {png_path}")


if __name__ == "__main__":
    comparison_df = run_comparison()
    print_table(comparison_df)
    save_outputs(comparison_df)