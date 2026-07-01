from ml.constants import SYMPTOMS_WEIGHT, VITALS_WEIGHT

def calculate_priority(symptoms_list, vitals_list, age, duration):
    score = 0

    for symptom in symptoms_list:
        score += SYMPTOMS_WEIGHT.get(symptom, 0)

    for vital in vitals_list:
        score += VITALS_WEIGHT.get(vital, 0)

    if age > 60:
        score += 1

    has_severe_symptom = False
    for s in symptoms_list:
        if SYMPTOMS_WEIGHT.get(s, 0) >= 2:
            has_severe_symptom = True

    if has_severe_symptom and duration <= 2:
        score += 1

    severe_score = 0

    for s in symptoms_list:
        w = SYMPTOMS_WEIGHT.get(s, 0)
        if w >= 2:
            severe_score += w

    for v in vitals_list:
        w = VITALS_WEIGHT.get(v, 0)
        if w >= 2:
            severe_score += w

    if score >= 4 and severe_score >= 2:
        return "high"
    elif score >= 2:
        return "medium"
    else:
        return "low"
