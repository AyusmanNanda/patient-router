from ml.predictors.patient_router import predict_patient_router

PREDICTORS = {
    "patient_router": predict_patient_router,
}

def predict(data: dict, method: str = "patient_router") -> dict :
    predictor = PREDICTORS.get(method)
    method = data.get("method", "patient_router")

    if predictor is None:
        raise ValueError("Unknown rules method")
    return predictor(data)