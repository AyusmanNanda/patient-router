from pathlib import Path
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "../data/data.csv"
REPORTS_DIR = BASE_DIR / "../reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

TEST_SIZE = 0.2
RANDOM_STATE = 42


def load_data():
    try:
        df = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        print(f"Failed to load data from {DATA_PATH}")
        exit(1)
    df["text"] = df["symptoms"] + " " + df["vitals"]
    return df


def evaluate():
    print("Loading data and model...")
    df = load_data()

    try:
        model = joblib.load(BASE_DIR / "models" / "model.pkl")
    except FileNotFoundError:
        print(f"Failed to load model from {BASE_DIR / 'models' / 'model.pkl'}")
        exit(1)

    X = df[["text", "age", "duration", "gender"]]  # CHANGED: was vectorizer.transform(df["text"])
    y = df["department"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    y_pred = model.predict(X_test)

    # accuracy
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nTest Accuracy: {accuracy * 100:.2f}%")

    # cross validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
    print(f"5-Fold CV Accuracy: {cv_scores.mean() * 100:.2f}% (+/- {cv_scores.std() * 100:.2f}%)")

    # per department breakdown
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # confusion matrix
    labels = sorted(y.unique())
    cm = confusion_matrix(y_test, y_pred, labels=labels)

    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=labels,
        yticklabels=labels,
    )
    plt.title("Confusion Matrix — Department Prediction")
    plt.ylabel("Actual")
    plt.xlabel("Predicted")
    plt.tight_layout()

    cm_path = REPORTS_DIR / "confusion_matrix.png"
    plt.savefig(cm_path)
    plt.close()
    print(f"\nConfusion matrix saved to {cm_path}")

    # per class confidence analysis
    print("\nPer Department Confidence (avg probability on correct predictions):")
    probs = model.predict_proba(X_test)
    classes = list(model.classes_)

    for dept in labels:
        mask = np.array(y_test == dept)
        if mask.sum() == 0:
            continue
        dept_idx = classes.index(dept)
        avg_confidence = probs[mask, dept_idx].mean()
        correct = (np.array(y_pred)[mask] == dept).sum()
        total = mask.sum()
        print(f"  {dept:<15} accuracy: {correct}/{total} ({correct/total*100:.1f}%)  avg confidence: {avg_confidence:.3f}")

    # save summary report
    report_text = (
        f"Model Evaluation Report\n"
        f"=======================\n"
        f"Test Size       : {TEST_SIZE * 100:.0f}%\n"
        f"Test Accuracy   : {accuracy * 100:.2f}%\n"
        f"CV Accuracy     : {cv_scores.mean() * 100:.2f}% (+/- {cv_scores.std() * 100:.2f}%)\n\n"
        f"Classification Report:\n"
        f"{classification_report(y_test, y_pred)}"
    )

    report_path = REPORTS_DIR / "evaluation_report.txt"
    with open(report_path, "w") as f:
        f.write(report_text)

    print(f"Full report saved to {report_path}")


if __name__ == "__main__":
    evaluate()