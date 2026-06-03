from ml.predict import predict_case

def predict(data):
    symptoms = data.get("symptoms", "").strip()
    vitals   = data.get("vitals", "").strip()
    age      = data.get("age")
    duration = data.get("duration")
    gender = data.get("gender", "male")

    if not symptoms:
        raise ValueError("Symptoms is required")

    if age is None or duration is None:
        raise ValueError("Age and duration are required")

    return predict_case(
            symptoms=symptoms,
            vitals=vitals,
            age=int(age),
            duration=int(duration),
            gender=gender
    )
