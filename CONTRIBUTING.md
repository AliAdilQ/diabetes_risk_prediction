# Contributing

Thanks for helping improve Diabetes Risk Prediction.

1. Fork [AliAdilQ/diabetes_risk_prediction](https://github.com/AliAdilQ/diabetes_risk_prediction).
2. Follow the setup commands in the README.
3. Create a branch: `git checkout -b feature/your-change`.
4. Make focused changes with descriptive names and useful docstrings. Follow PEP 8.
5. Keep input definitions in `app/features.py` and use the shared inference path.
6. Run `python -m pytest -q`. If changing ML code, regenerate data and retrain first.
7. For UI changes, inspect desktop and mobile layouts and capture real screenshots.
8. Commit your changes, push your branch, and open a pull request describing the
   resulting behavior and the checks you ran.

Preserve educational wording, synthetic-data labeling, and the medical disclaimer.
Never include personal health records, secret keys, local databases, or `.env` files.
Do not upload untrusted pickle files. Keep generated model metrics consistent with
their artifact and dataset. Report security issues through the process in SECURITY.md.
