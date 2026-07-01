from ml.constants import EMERGENCY_SYMPTOMS, EMERGENCY_VITALS


def detect_emergency(symptoms_list, vitals_list):

    for symptom in symptoms_list:
        if symptom in EMERGENCY_SYMPTOMS:
            return True

    for vital in vitals_list:
        if vital in EMERGENCY_VITALS:
            return True

    return False