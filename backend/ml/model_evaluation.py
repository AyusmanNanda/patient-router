from pathlib import Path
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from ml.constants import DEPARTMENTS 

BASE_DIR    = Path(__file__).resolve().parent
DATA_PATH   = BASE_DIR / "../data/data.csv"
REPORTS_DIR = BASE_DIR / "../reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

TEST_SIZE     = 0.2
RANDOM_STATE  = 42

# ── Real-world edge cases ──────────────────────────────────────────────────────
# These use the SAME canonical tag format the frontend sends (symptoms joined
# with ", ", vitals joined with ", ") — matching predict_case() input exactly.
# They test realistic age/duration combinations and cross-department overlaps
# that rarely appear in the evenly-distributed synthetic training data.
# Format: (symptoms_str, vitals_str, age, duration_days, gender, true_department)
REAL_WORLD_CASES = [
    # ── Typical clean presentations ──
    ("chest pain, breathlessness",              "bp_high, hr_high", 62, 2,  "male",   "cardiology"),
    ("chest pain, sweating, fatigue",           "bp_high",          70, 1,  "female", "cardiology"),
    ("breathlessness, fatigue",                 "hr_high",          55, 3,  "male",   "cardiology"),
    ("cough, fever, breathlessness",            "temp_high",        35, 7,  "female", "pulmonology"),
    ("cough, fatigue",                          "temp_high, hr_high",28, 10, "male",   "pulmonology"),
    ("headache, dizziness, blurred vision",     "bp_low",           45, 3,  "female", "neurology"),
    ("headache, confusion",                     "bp_high",          60, 2,  "male",   "neurology"),
    ("joint pain, swelling, stiffness",         "normal",           55, 30, "male",   "orthopedics"),
    ("joint pain, limited movement",            "normal",           63, 45, "female", "orthopedics"),
    ("abdominal pain, nausea, vomiting",        "normal",           30, 1,  "female", "gastrology"),
    ("abdominal pain, diarrhea",                "normal",           25, 2,  "male",   "gastrology"),
    ("fever, body pain, weakness",              "temp_high",        22, 3,  "male",   "general"),
    ("fever, fatigue",                          "temp_high",        19, 2,  "female", "general"),

    # ── Edge: single symptom only ──
    ("fatigue",                                 "",                 35, 5,  "male",   "general"),
    ("chest pain",                              "",                 58, 1,  "male",   "cardiology"),
    ("headache",                                "",                 40, 2,  "female", "neurology"),
    ("cough",                                   "",                 30, 7,  "male",   "pulmonology"),

    # ── Edge: old patients with minimal symptoms ──
    ("fatigue, dizziness",                      "bp_low",           75, 4,  "female", "neurology"),
    ("chest pain",                              "bp_high",          72, 1,  "male",   "cardiology"),
    ("weakness, fatigue",                       "normal",           68, 7,  "female", "general"),

    # ── Edge: young patients ──
    ("joint pain, swelling",                    "normal",           22, 14, "male",   "orthopedics"),
    ("abdominal pain, vomiting, nausea",        "normal",           18, 1,  "female", "gastrology"),

    # ── Hard: cross-department symptom overlap ──
    # breathlessness appears in both cardiology and pulmonology
    ("breathlessness, cough, fever",            "temp_high",        40, 7,  "male",   "pulmonology"),
    ("breathlessness, chest pain",              "hr_high",          55, 1,  "female", "cardiology"),
    # fatigue appears in cardiology, pulmonology, general
    ("fatigue, cough",                          "temp_high",        33, 5,  "male",   "pulmonology"),
    ("fatigue, chest pain",                     "bp_high",          60, 3,  "male",   "cardiology"),
    ("fatigue, fever, body pain",               "temp_high",        27, 3,  "female", "general"),
    # nausea appears in gastrology and neurology
    ("nausea, headache, dizziness",             "bp_low",           42, 2,  "female", "neurology"),
    ("nausea, abdominal pain, vomiting",        "normal",           31, 1,  "male",   "gastrology"),
    # dizziness + bp_low could be neurology or cardiology
    ("dizziness, fatigue",                      "bp_low",           50, 3,  "male",   "neurology"),

    # ── Hard: chronic vs acute same symptoms ──
    ("joint pain, stiffness",                   "normal",           58, 90, "female", "orthopedics"),
    ("chest pain, breathlessness",              "normal",           45, 1,  "male",   "cardiology"),

    # ── Hard: vitals contradict symptoms ──
    ("chest pain, sweating",                    "normal",           65, 2,  "male",   "cardiology"),
    ("cough, breathlessness",                   "normal",           38, 14, "female", "pulmonology"),
]


def load_data():
    try:
        df = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        print(f"[ERROR] data.csv not found at {DATA_PATH}")
        exit(1)
    df["text"] = df["symptoms"] + " " + df["vitals"]
    return df


def evaluate_synthetic(model, df):
    """Standard evaluation on held-out synthetic test split."""
    X = df[["text", "age", "duration", "gender"]]
    y = df["department"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    classes = list(model.classes_)

    accuracy  = accuracy_score(y_test, y_pred)
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")

    print("\n" + "═"*55)
    print("  SYNTHETIC TEST SET (held-out 20%)")
    print("═"*55)
    print(f"  Test Accuracy : {accuracy * 100:.2f}%")
    print(f"  5-Fold CV     : {cv_scores.mean()*100:.2f}% (±{cv_scores.std()*100:.2f}%)")
    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    print("  Per-Department Confidence:")
    labels = sorted(y.unique())
    per_dept = {}
    for dept in labels:
        mask      = np.array(y_test == dept)
        dept_idx  = classes.index(dept)
        avg_conf  = y_proba[mask, dept_idx].mean()
        correct   = (np.array(y_pred)[mask] == dept).sum()
        total     = mask.sum()
        per_dept[dept] = {"correct": correct, "total": total, "avg_conf": avg_conf}
        print(f"    {dept:<15} {correct:>4}/{total}  ({correct/total*100:.1f}%)  "
              f"avg conf: {avg_conf:.3f}")

    return y_test, y_pred, accuracy, cv_scores, per_dept


def evaluate_real_world(model):
    """
    Evaluate on hand-crafted edge cases using the exact same input format
    the frontend sends: canonical comma-separated symptom/vital tags.
    Tests realistic age/duration combinations and cross-department overlaps.
    """
    rows, true = [], []
    for (sym, vit, age, dur, gen, dept) in REAL_WORLD_CASES:
        text = (sym + " " + vit).strip()
        rows.append({"text": text, "age": age, "duration": dur, "gender": gen})
        true.append(dept)

    X_rw    = pd.DataFrame(rows)
    y_pred  = model.predict(X_rw)
    y_proba = model.predict_proba(X_rw)
    classes = list(model.classes_)

    accuracy = accuracy_score(true, y_pred)

    print("\n" + "═"*55)
    print("  EDGE-CASE TEST SET (hand-crafted)")
    print("═"*55)
    print(f"  Accuracy : {accuracy * 100:.2f}%  ({sum(p==t for p,t in zip(y_pred,true))}/{len(true)} correct)\n")

    print(f"  {'Symptoms (truncated)':<35} {'True':<14} {'Predicted':<14} {'Conf':>6}  OK?")
    print("  " + "-"*76)
    wrong_cases = []
    for i, ((sym, vit, age, dur, gen, true_dept), pred) in enumerate(zip(REAL_WORLD_CASES, y_pred)):
        dept_idx = classes.index(pred)
        conf     = y_proba[i, dept_idx]
        ok       = "✓" if pred == true_dept else "✗"
        snippet  = (sym[:33] + "…") if len(sym) > 33 else sym
        print(f"  {snippet:<35} {true_dept:<14} {pred:<14} {conf:>5.2f}  {ok}")
        if pred != true_dept:
            wrong_cases.append((sym, vit, true_dept, pred, conf))

    if wrong_cases:
        print(f"\n  Failures ({len(wrong_cases)}):")
        for sym, vit, true_dept, pred, conf in wrong_cases:
            print(f"    • symptoms={sym!r}  vitals={vit!r}")
            print(f"      expected={true_dept}  got={pred}  conf={conf:.2f}")

    print("\n  Classification Report (edge cases):")
    print(classification_report(true, y_pred, zero_division=0))

    return accuracy, true, list(y_pred)


def plot_reports(y_test_syn, y_pred_syn, true_rw, pred_rw,
                 acc_syn, acc_rw, cv_scores, per_dept):
    labels = sorted(set(y_test_syn))

    fig = plt.figure(figsize=(18, 12))
    fig.suptitle("Patient Router — Model Evaluation", fontsize=15, fontweight="bold", y=0.98)
    gs  = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

    # ── 1. Synthetic confusion matrix ──
    ax1 = fig.add_subplot(gs[0, 0])
    cm  = confusion_matrix(y_test_syn, y_pred_syn, labels=labels)
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=labels, yticklabels=labels, ax=ax1, cbar=False)
    ax1.set_title("Confusion matrix\n(synthetic test set)", fontsize=11)
    ax1.set_ylabel("Actual"); ax1.set_xlabel("Predicted")
    ax1.tick_params(axis="x", rotation=35)

    # ── 2. Real-world confusion matrix ──
    ax2 = fig.add_subplot(gs[0, 1])
    rw_labels = sorted(set(true_rw) | set(pred_rw))
    cm_rw = confusion_matrix(true_rw, pred_rw, labels=rw_labels)
    sns.heatmap(cm_rw, annot=True, fmt="d", cmap="Oranges",
                xticklabels=rw_labels, yticklabels=rw_labels, ax=ax2, cbar=False)
    ax2.set_title("Confusion matrix\n(edge cases)", fontsize=11)
    ax2.set_ylabel("Actual"); ax2.set_xlabel("Predicted")
    ax2.tick_params(axis="x", rotation=35)

    # ── 3. Synthetic vs Real-world accuracy bar ──
    ax3 = fig.add_subplot(gs[0, 2])
    bars = ax3.bar(["Synthetic\n(test split)", "Edge cases\n(hand-crafted)"],
                   [acc_syn * 100, acc_rw * 100],
                   color=["#3b82f6", "#f97316"], width=0.45, edgecolor="white")
    ax3.set_ylim(0, 110)
    ax3.set_ylabel("Accuracy (%)")
    ax3.set_title("Synthetic vs edge-case\naccuracy gap", fontsize=11)
    for bar, val in zip(bars, [acc_syn * 100, acc_rw * 100]):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                 f"{val:.1f}%", ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax3.axhline(y=acc_syn*100, color="#3b82f6", linestyle="--", alpha=0.3, linewidth=1)

    # ── 4. Per-department accuracy (synthetic) ──
    ax4 = fig.add_subplot(gs[1, 0])
    depts     = list(per_dept.keys())
    dept_accs = [per_dept[d]["correct"]/per_dept[d]["total"]*100 for d in depts]
    colors    = ["#22c55e" if a >= 97 else "#f97316" if a >= 90 else "#ef4444" for a in dept_accs]
    ax4.barh(depts, dept_accs, color=colors, edgecolor="white")
    ax4.set_xlim(0, 110)
    ax4.set_xlabel("Accuracy (%)")
    ax4.set_title("Per-department accuracy\n(synthetic)", fontsize=11)
    for i, (dept, acc) in enumerate(zip(depts, dept_accs)):
        ax4.text(acc + 0.5, i, f"{acc:.1f}%", va="center", fontsize=9)
    ax4.axvline(x=90, color="gray", linestyle="--", alpha=0.4, linewidth=1)

    # ── 5. Per-department avg confidence ──
    ax5 = fig.add_subplot(gs[1, 1])
    confs  = [per_dept[d]["avg_conf"] for d in depts]
    colors2= ["#22c55e" if c >= 0.95 else "#f97316" if c >= 0.85 else "#ef4444" for c in confs]
    ax5.barh(depts, confs, color=colors2, edgecolor="white")
    ax5.set_xlim(0, 1.15)
    ax5.set_xlabel("Avg confidence (correct preds)")
    ax5.set_title("Per-department confidence\n(synthetic)", fontsize=11)
    for i, (dept, conf) in enumerate(zip(depts, confs)):
        ax5.text(conf + 0.005, i, f"{conf:.3f}", va="center", fontsize=9)
    ax5.axvline(x=0.60, color="red",  linestyle="--", alpha=0.4, linewidth=1, label="threshold 0.60")
    ax5.legend(fontsize=8)

    # ── 6. CV score distribution ──
    ax6 = fig.add_subplot(gs[1, 2])
    folds = [f"Fold {i+1}" for i in range(len(cv_scores))]
    ax6.bar(folds, cv_scores * 100, color="#8b5cf6", edgecolor="white")
    ax6.axhline(y=cv_scores.mean()*100, color="#8b5cf6", linestyle="--",
                linewidth=1.5, label=f"mean {cv_scores.mean()*100:.2f}%")
    ax6.set_ylim(min(cv_scores)*100 - 1, 101)
    ax6.set_ylabel("Accuracy (%)")
    ax6.set_title("5-fold cross-validation\nstability", fontsize=11)
    ax6.legend(fontsize=8)

    plt.savefig(REPORTS_DIR / "evaluation_report.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Charts saved → {REPORTS_DIR / 'evaluation_report.png'}")


def save_text_report(acc_syn, cv_scores, acc_rw, per_dept, y_test_syn, y_pred_syn):
    gap = (acc_syn - acc_rw) * 100
    lines = [
        "Model Evaluation Report",
        "=" * 55,
        f"Synthetic test accuracy  : {acc_syn*100:.2f}%",
        f"5-Fold CV accuracy       : {cv_scores.mean()*100:.2f}% (±{cv_scores.std()*100:.2f}%)",
        f"Edge-case accuracy       : {acc_rw*100:.2f}%",
        f"Generalisation gap       : {gap:.1f}pp  ← cross-dept overlap performance",
        "",
        "Per-Department (synthetic):",
        f"  {'Department':<15} {'Acc':>7}  {'Avg Conf':>9}",
        "  " + "-"*35,
        ]
    for dept, v in per_dept.items():
        acc = v["correct"]/v["total"]*100
        lines.append(f"  {dept:<15} {acc:>6.1f}%  {v['avg_conf']:>9.3f}")

    lines += [
        "",
        "Classification Report (synthetic):",
        classification_report(y_test_syn, y_pred_syn, zero_division=0),
    ]

    path = REPORTS_DIR / "evaluation_report.txt"
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"  Text report saved → {path}")

import json

def save_json_report(acc_syn, cv_scores, acc_rw):
    gap = (acc_syn - acc_rw) * 100

    report = {
        "synthetic_accuracy": round(acc_syn * 100, 2),
        "cv_accuracy": round(cv_scores.mean() * 100, 2),
        "cv_std": round(cv_scores.std() * 100, 2),
        "edge_case_accuracy": round(acc_rw * 100, 2),
        "generalization_gap": round(gap, 1),

        "total_edge_cases": 34,
        "passed_edge_cases": round(acc_rw * 34),
        "failed_edge_cases": 34 - round(acc_rw * 34)
    }

    output_file = REPORTS_DIR / "evaluation_metrics.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    print(f"  JSON report saved → {output_file}")


def evaluate():
    print("Loading data and model…")
    df    = load_data()
    model = joblib.load(BASE_DIR / "models" / "model.pkl")

    y_test_syn, y_pred_syn, acc_syn, cv_scores, per_dept = evaluate_synthetic(model, df)
    acc_rw, true_rw, pred_rw                             = evaluate_real_world(model)

    gap = (acc_syn - acc_rw) * 100
    print("\n" + "═"*55)
    print(f"  GENERALISATION GAP : {gap:.1f} percentage points")
    print(f"  (synthetic {acc_syn*100:.1f}%  →  real-world {acc_rw*100:.1f}%)")
    if gap > 20:
        print("  ⚠  Large gap — extractor normalisation will help significantly")
    elif gap > 10:
        print("  ⚠  Moderate gap — alias expansion + fuzzy match will help")
    else:
        print("  ✓  Small gap — model generalises reasonably well")
    print("═"*55)

    plot_reports(y_test_syn, y_pred_syn, true_rw, pred_rw,
                 acc_syn, acc_rw, cv_scores, per_dept)
    save_text_report(acc_syn, cv_scores, acc_rw, per_dept, y_test_syn, y_pred_syn)
    save_json_report(acc_syn, cv_scores, acc_rw)


if __name__ == "__main__":
    evaluate()