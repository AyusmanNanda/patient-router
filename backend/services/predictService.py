from ml.engine import predict as predict_engine


def predict_case(data: dict):
    symptoms = data.get("symptoms", "").strip()
    age = data.get("age")
    duration = data.get("duration")
    method = data.get("method", "patient_router")

    if not symptoms:
        raise ValueError("Symptoms are required")

    if age is None:
        raise ValueError("Age is required")

    if duration is None:
        raise ValueError("Duration is required")

    return predict_engine(data, method)