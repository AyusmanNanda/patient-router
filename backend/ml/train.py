import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.feature_extraction.text import CountVectorizer
import joblib

df = pd.read_csv("../data/data.csv")

X = (df["symptoms"] + " " + df["vitals"])
y = df["department"]

vectorizer = CountVectorizer()
X_vectorizer = vectorizer.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_vectorizer, y, test_size = 0.2, random_state = 42)

model = RandomForestClassifier()
model.fit(X_train, y_train)

predict = model.predict(X_test)
print("Accuracy: ", accuracy_score(y_test, predict))

sample = ["chest pain breathlessness bp_high hr_high"]
sample_vec = vectorizer.transform(sample)

print("Prediction: ", model.predict(sample_vec)[0])
print(df["department"].value_counts())

joblib.dump(model, "./models/model.pkl")
joblib.dump(vectorizer, "./models/vectorizer.pkl")