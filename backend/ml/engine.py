from ml.predictors.patient_router import predict_patient_router
from ml.predictors.llm import predict_llm
from ml.predictors.hybrid import predict_hybrid

PREDICTORS = {
    "patient_router": predict_patient_router,
    "llm": predict_llm,
    "hybrid": predict_hybrid,
}

def predict(data: dict, method: str = "patient_router") -> dict:
    method = data.get("method", method)

    predictor = PREDICTORS.get(method)

    if predictor is None:
        raise ValueError(f"Unknown prediction method: {method}")

    return predictor(data)