import random
import pandas as pd
from pathlib import Path
from ml.constants import (SAMPLE_SIZE, DEPARTMENTS,
                       GENDERS, OPPOSITES,
                       SYMPTOMS_WEIGHT, VITALS_WEIGHT, DEPT_HISTORY_BIAS, KNOWN_HISTORY
                       )

output_path = Path(__file__).resolve().parent.parent / "data" / "data.csv"
output_path.parent.mkdir(parents=True, exist_ok=True)

all_symptoms = set()
for department in DEPARTMENTS.values():
    for symptom in department["symptoms"]:
        all_symptoms.add(symptom)

ALL_SYMPTOMS = sorted(list(all_symptoms))
ALL_VITALS = list(OPPOSITES.keys())

def add_overlap_symptom(base, dept):
    other_depts = [d for d in DEPARTMENTS if d != dept]

    overlap_dept = random.choice(other_depts)

    symptom = random.choice(
        DEPARTMENTS[overlap_dept]["symptoms"]
    )

    if symptom not in base:
        base.append(symptom)

def generate_symptoms(dept):
    symptoms_list = DEPARTMENTS[dept]["symptoms"]
    k = random.randint(
        1,
        min(4, len(symptoms_list))
    )

    base = random.sample(symptoms_list, k)

    if random.random() < 0.2 and len(base) > 1:
        base.pop()

    if random.random() < 0.4:
        add_overlap_symptom(base, dept)

    return base


def generate_vitals(dept):
    vitals_list = [v for v in DEPARTMENTS[dept]["vitals"] if v != "normal"]
    if random.random() < 0.05:
        return ["unknown"]

    if random.random() < 0.30:
        return ["normal"]

    if not vitals_list:
        return ["normal"]

    count = min(random.randint(1, 2), len(vitals_list))
    base = random.sample(vitals_list, count)

    if random.random() < 0.15 and base != ["normal"]:
        error_idx = random.randint(0, len(base) - 1)
        base[error_idx] = OPPOSITES.get(base[error_idx], base[error_idx])

    if random.random() < 0.40:
        extra = random.choice(ALL_VITALS)
        if extra not in base and OPPOSITES.get(extra) not in base:
            base.append(extra)

    return base

def generate_history(dept):
    history = []
    biased = DEPT_HISTORY_BIAS.get(dept, [])

    for condition in KNOWN_HISTORY:
        prob = 0.35 if condition in biased else 0.08
        if random.random() < prob:
            history.append(condition)

    if random.random() < 0.15 and history:
        unrelated = [c for c in KNOWN_HISTORY if c not in biased]
        if unrelated:
            extra = random.choice(unrelated)
            if extra not in history:
                history.append(extra)
    if random.random() < 0.10 and len(history) > 1:
        history.pop(random.randint(0, len(history) - 1))

    if random.random() < 0.20:
        return []

    return history

def compute_priority(symptoms, vitals, age, duration):
    score = 0

    for symptom in symptoms:
        score += SYMPTOMS_WEIGHT.get(symptom, 0)

    for vital in vitals:
        score += VITALS_WEIGHT.get(vital, 0)

    if age > 60:
        score += 1

    if any(s in SYMPTOMS_WEIGHT for s in symptoms) and duration <= 2:
        score += 1

    if score >= 4:
        return "high"
    elif score >= 2:
        return "medium"
    else:
        return "low"


def generate_row(department):
    department_config = DEPARTMENTS[department]

    age = random.randint(*department_config["age_range"])
    duration = random.randint(*department_config["duration_range"])
    gender = random.choice(GENDERS)

    symptoms = generate_symptoms(department)
    vitals = generate_vitals(department)
    history = generate_history(department)

    return {
        "age": age,
        "duration": duration,
        "symptoms": ", ".join(symptoms),
        "vitals": ", ".join(vitals),
        "history": ", ".join(history),
        "gender": gender,
        "priority": compute_priority(symptoms, vitals, age, duration),
        "department": department
    }


def generate_dataset(n):
    departments = list(DEPARTMENTS.keys())
    rows_per_dept = n // len(departments)
    remainder = n % len(departments)

    rows = []

    for i, dept in enumerate(departments):
        count = rows_per_dept + (1 if i < remainder else 0)
        for _ in range(count):
            rows.append(generate_row(dept))

    df = pd.DataFrame(rows)
    return df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle


if __name__ == "__main__":
    df = generate_dataset(SAMPLE_SIZE)
    df.to_csv(output_path, index=False)

    print(f"Dataset generated: {SAMPLE_SIZE} rows at {output_path}")
    print(f"\nDepartment distribution:\n{df['department'].value_counts()}")
    print(f"\nPriority distribution:\n{df['priority'].value_counts()}")