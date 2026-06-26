from ml.constants import HISTORY_WEIGHTS, KNOWN_HISTORY


def analyze_history(history_list):
    score = 0

    for condition in history_list:
        score += HISTORY_WEIGHTS.get(condition, 0)

    high_risk = False
    for condition in history_list:
        if HISTORY_WEIGHTS.get(condition, 0) >= 9:
            high_risk = True

    if score >= 10:
        high_risk = True

    return score, high_risk