"""Generate deterministic, fictional values and labels; no clinical records."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SEED = 42


def generate_dataset(rows=600):
    rng = np.random.default_rng(SEED)
    age = np.clip(rng.normal(43, 16, rows), 18, 85).astype(int)
    bmi = np.clip(rng.normal(30, 7, rows), 16, 55).round(1)
    glucose = np.clip(rng.normal(119, 34, rows) + 0.45 * (bmi - 30), 45, 245).round(0)
    pedigree = np.clip(rng.gamma(2.2, 0.23, rows), 0.05, 2.7).round(3)
    pregnancies = np.minimum(rng.poisson(np.clip((age - 18) / 12, 0, 5)), 15)
    pressure = np.clip(rng.normal(72, 11, rows) + 0.12 * (age - 40), 35, 115).round(0)
    skin = np.clip(rng.normal(27, 9, rows) + 0.35 * (bmi - 30), 5, 70).round(0)
    insulin = np.clip(rng.lognormal(4.7, 0.6, rows) + 0.6 * (glucose - 120), 12, 700).round(0)
    # An invented probabilistic rule creates demonstration labels, not diagnoses.
    logit = (-0.8 + 0.045 * (glucose - 120) + 0.09 * (bmi - 30)
             + 0.025 * (age - 40) + 0.8 * (pedigree - 0.5)
             + 0.06 * (pregnancies - 2))
    outcome = rng.binomial(1, 1 / (1 + np.exp(-logit)))
    frame = pd.DataFrame({
        "Pregnancies": pregnancies, "Glucose": glucose, "BloodPressure": pressure,
        "SkinThickness": skin, "Insulin": insulin, "BMI": bmi,
        "DiabetesPedigreeFunction": pedigree, "Age": age, "Outcome": outcome,
    })
    # Include missing-value sentinels to exercise training-time cleanup.
    for column in ("Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"):
        frame.loc[rng.choice(rows, size=max(1, rows // 40), replace=False), column] = 0
    return frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=600)
    args = parser.parse_args()
    if args.rows < 300:
        parser.error("Use at least 300 demo rows.")
    target = ROOT / "data" / "diabetes_sample.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    frame = generate_dataset(args.rows)
    frame.to_csv(target, index=False, lineterminator="\n")
    print(f"Generated {len(frame)} synthetic rows: {target}")


if __name__ == "__main__":
    main()
