import random
import pandas as pd

SAMPLE_SIZE = 500 # size of dataset


GENDERS = ['male', 'female']

DEPARTMENTS = {
    "cardiology" : {
        "symptoms": ["chest pain", "breathlessness", "fatigue", "sweating"],
        "vitals": ["bp_high", "hr_high"],
        "age_range": (45, 80),
        "duration_range": (1, 5)
    },
    "pulmonology" : {
        "symptoms": ["cough", "breathlessness", "fever", "fatigue"],
        "vitals": ["temp_high", "hr_high"],
        "age_range": (20, 70),
        "duration_range": (1, 7)
    },
    "neurology" : {
        "symptoms": ["headache", "dizziness", "confusion", "blurred vision"],
        "vitals": ["bp_low", "bp_high"],
        "age_range": (30, 80),
        "duration_range": (1, 10)
    },
    "orthopedics" : {
        "symptoms": ["joint pain", "swelling", "stiffness", "limited movement"],
        "vitals": ["normal"],
        "age_range": (40, 85),
        "duration_range": (7, 30)
    },
    "gastrology" : {
        "symptoms": ["abdominal pain", "nausea", "vomiting", "diarrhea"],
        "vitals": ["normal"],
        "age_range": (20, 65),
        "duration_range": (1, 5)
    },
    "general" : {
        "symptoms": ["fever", "body pain", "weakness", "fatigue"],
        "vitals": ["temp_high"],
        "age_range": (15, 60),
        "duration_range": (1, 5)
    }
}
all_symptoms = set()
for department in DEPARTMENTS.values():
    for symptom in department["symptoms"]:
        all_symptoms.add(symptom)

ALL_SYMPTOMS = sorted(list(all_symptoms))


OPPOSITES = {
    "bp_high" : "bp_low",
    "hr_high" : "hr_low",
    "temp_high" : "temp_low",
    "bp_low" : "bp_high",
    "hr_low" : "hr_high",
    "temp_low" : "temp_high",
}
ALL_VITALS = list(OPPOSITES.keys())

def generate_symptoms(dept):
    symptoms_list = DEPARTMENTS[dept]["symptoms"]
    base = random.sample(symptoms_list, k=min(2, len(symptoms_list)))

    #add noise
    if random.random() < 0.3:
        noise = random.choice(ALL_SYMPTOMS)
        if noise not in base:
            base.append(noise)

    return base

def generate_vitals(dept):
    vitals_list = DEPARTMENTS[dept]["vitals"]

    base = []
    for vital in random.sample(vitals_list, k=len(vitals_list)):
        if OPPOSITES.get(vital) not in base:
            base.append(vital)
        if len(base) == 2:
            break
    if random.random() < 0.3:
        extra = random.choice(ALL_VITALS)
        if extra not in base and OPPOSITES.get(extra) not in base:
            base.append(extra)
    if "normal" in base and len(base) > 1:
        base.remove("normal")
    return base

SYMPTOMS_WEIGHT = {
    "chest pain": 2,
    "breathlessness": 2,
}
VITALS_WEIGHT = {
    "bp_high": 2,
    "hr_high": 1,
}

def compute_priority(symptoms, vitals, age):
    symptoms = set(symptoms)
    vitals = set(vitals)

    score = 0

    for symptom in symptoms:
        score += SYMPTOMS_WEIGHT.get(symptom, 0)

    for vital in vitals:
        score += VITALS_WEIGHT.get(vital, 0)

    if age > 60:
        score += 1


    if score >= 4:
        return "high"
    elif score >= 2:
        return "medium"
    else:
        return "low"



def generate_row():
    department = random.choice(list(DEPARTMENTS))
    department_config = DEPARTMENTS[department]

    age = random.randint(*department_config["age_range"])
    duration = random.randint(*department_config["duration_range"])
    gender = random.choice(GENDERS)

    symptoms = generate_symptoms(department)
    vitals = generate_vitals(department)

    return {
        "age": age,
        "duration": duration,
        "symptoms": ", ".join(map(str, symptoms)),
        "vitals": ", ".join(map(str, vitals)),
        "gender": gender,
        "priority": compute_priority(symptoms, vitals, age),
        "department": department

    }



def generate_dataset(n):
    return pd.DataFrame([generate_row() for _ in range(n)])

if __name__ == "__main__":
    df = generate_dataset(SAMPLE_SIZE)

    output_path = "../data/data.csv"
    df.to_csv(output_path, index=False)

    print(f"Dataset generated {SAMPLE_SIZE} rows at {output_path}")




