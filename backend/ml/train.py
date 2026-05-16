import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.feature_extraction.text import CountVectorizer
import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv("../data/data.csv")

X = (df["symptoms"] + " " + df["vitals"])
y = df["department"]


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 42, stratify = y)

vectorizer = CountVectorizer()
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

model = RandomForestClassifier(n_estimators = 100, random_state = 42)
model.fit(X_train_vec, y_train)

train_accuracy = accuracy_score(y_train, model.predict(X_train_vec))
test_accuracy = accuracy_score(y_test, model.predict(X_test_vec))

print(f"Train Accuracy: {train_accuracy * 100:.2f}%")
print(f"Test Accuracy: {test_accuracy * 100:.2f}%")

if train_accuracy - test_accuracy < 0.05:
    print("Warning: possible overfitting detected")

print(f"\nDepartment distribution:\n{df['department'].value_counts()}")

joblib.dump(model, BASE_DIR / "models/model.pkl")
joblib.dump(vectorizer, BASE_DIR / "models/vectorizer.pkl")

print("\nModel and vectorizer saved")