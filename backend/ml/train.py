import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.feature_extraction.text import CountVectorizer
import joblib
from pathlib import Path

df = pd.read_csv("../data/data.csv")

X = (df["symptoms"] + " " + df["vitals"])
y = df["department"]

vectorizer = CountVectorizer()
X_vectorizer = vectorizer.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_vectorizer, y, test_size = 0.2, random_state = 42)

model = RandomForestClassifier(random_state = 42)
model.fit(X_train, y_train)

pred = model.predict(X_test)
print("Accuracy: ", accuracy_score(y_test, pred))

print(df["department"].value_counts())

BASE_DIR = Path(__file__).resolve().parent

joblib.dump(model, BASE_DIR / "models/model.pkl")
joblib.dump(vectorizer, BASE_DIR / "models/vectorizer.pkl")