from ml.predictors.patient_router import predict_patient_router
from ml.predictors.llm import predict_llm
from ml.constants import CONFIDENCE_THRESHOLD

def predict_hybrid(data: dict) -> dict:
    ml_result = predict_patient_router(data)
    if ml_result["confidence"] >= CONFIDENCE_THRESHOLD:
        return ml_result

    return predict_llm(data)
