"""One feature schema shared by validation, inference, and templates."""

from dataclasses import dataclass

DISCLAIMER = (
    "This application is for educational and demonstration purposes only. "
    "It is not a medical diagnosis tool and should not replace professional medical advice."
)


@dataclass(frozen=True)
class Feature:
    key: str
    column: str
    label: str
    unit: str
    minimum: float
    maximum: float
    example: float
    help: str
    icon: str
    integer: bool = False


FEATURES = (
    Feature("pregnancies", "Pregnancies", "Pregnancies", "count", 0, 20, 2,
            "Number of pregnancies. Use 0 when not applicable.", "person", True),
    Feature("glucose", "Glucose", "Glucose", "mg/dL", 40, 250, 120,
            "A demo glucose measurement; use mg/dL.", "droplet"),
    Feature("blood_pressure", "BloodPressure", "Blood pressure", "mm Hg", 30, 150, 75,
            "Diastolic blood pressure, in mm Hg.", "heart-pulse"),
    Feature("skin_thickness", "SkinThickness", "Skin thickness", "mm", 0, 100, 25,
            "Triceps skinfold thickness. 0 is treated as missing.", "layers"),
    Feature("insulin", "Insulin", "Insulin", "µU/mL", 0, 900, 100,
            "Demo serum insulin value. 0 is treated as missing.", "activity"),
    Feature("bmi", "BMI", "Body mass index", "kg/m²", 10, 70, 26.5,
            "Weight in kilograms divided by height in meters squared.", "speedometer2"),
    Feature("diabetes_pedigree", "DiabetesPedigreeFunction", "Diabetes pedigree", "score",
            0, 3, 0.45, "A dataset-specific family-history score; use the example for this demo.",
            "diagram-3"),
    Feature("age", "Age", "Age", "years", 18, 100, 35,
            "Age in years. This demonstration accepts adults only.", "calendar3", True),
)
FEATURE_COLUMNS = [feature.column for feature in FEATURES]
ZERO_AS_MISSING = ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]
