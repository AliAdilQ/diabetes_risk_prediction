# Diabetes Risk Prediction

![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-193A40?logo=flask&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.7-F7931E?logo=scikitlearn&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?logo=bootstrap&logoColor=white)
[![Tests](https://github.com/AliAdilQ/diabetes_risk_prediction/actions/workflows/tests.yml/badge.svg)](https://github.com/AliAdilQ/diabetes_risk_prediction/actions/workflows/tests.yml)
[![MIT License](https://img.shields.io/badge/License-MIT-0C9488)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-AliAdilQ%2Fdiabetes__risk__prediction-181717?logo=github)](https://github.com/AliAdilQ/diabetes_risk_prediction)

**Eight inputs. Four algorithms. A complete path from data to a working application.**

DiabetesAI is a responsive Flask portfolio application that demonstrates diabetes-risk
classification with **synthetic data**. It combines a reproducible scikit-learn pipeline,
validated predictions, persistent history, and a protected analytics workspace. Built by
[AliAdilQ](https://github.com/AliAdilQ).

> This application is for educational and demonstration purposes only. It is not a medical diagnosis tool and should not replace professional medical advice.

## A look inside

### Home
![Home Page](screenshots/home.png)

<details>
<summary><strong>Prediction form and result</strong></summary>

**Validated inputs with units, help text, and an example preset**
![Prediction Form](screenshots/prediction.png)

**An estimated probability with a transparent input summary**
![Prediction Result](screenshots/result.png)

</details>

<details>
<summary><strong>Admin login and analytics workspace</strong></summary>

**Protected administrator access**
![Admin Login](screenshots/admin-login.png)

**Populated analytics, charts, and recent predictions**
![Admin Dashboard](screenshots/admin-dashboard.png)

</details>

These are actual browser captures of the running application at 1440px desktop width.
Frontend libraries, icons, and the Manrope font are served locally; the app needs no CDN
connection after installation.

## Features

- Responsive home, prediction, result, about, model information, and themed error pages.
- Eight validated inputs with units, useful help text, loading feedback, and a demo preset.
- Estimated probability and neutral **Lower Predicted Risk / Higher Predicted Risk** wording.
- Each successful web or JSON prediction is saved with model name, version, source, and UTC timestamp.
- Admin authentication with hashed passwords, CSRF protection, protected routes, and POST logout.
- Total, higher/lower class, average probability, and today's prediction statistics.
- Chart.js doughnut, daily activity, and age-distribution charts; zero-filled 14-day timelines.
- Paginated records with search, class/date filters, allowlisted sorting, details, deletion confirmation, and filtered CSV export.
- Public and admin model reports with real metrics and a confusion matrix.
- Reproducible synthetic dataset, model comparison, and idempotent demo database seeding.
- CSRF-protected JSON endpoint, request limits, local static assets, and security headers.
- pytest coverage and a GitHub Actions workflow on Python 3.11 and 3.12.

## Technology

| Layer | Tools |
| --- | --- |
| Application | Python 3.11–3.12, Flask, application factory, blueprints |
| Authentication & forms | Flask-Login, Flask-WTF, WTForms, Werkzeug scrypt hashes |
| Database | Flask-SQLAlchemy, SQLAlchemy, SQLite by default |
| Machine learning | scikit-learn, Pandas, NumPy, Joblib |
| Interface | HTML5, CSS3, JavaScript, Bootstrap 5, Bootstrap Icons, Chart.js |
| Operations | python-dotenv, Flask-Limiter, Waitress, pytest, GitHub Actions |

## Quick start

Install **Python 3.11 or 3.12** and Git first. Python 3.8 is not supported by these pinned dependencies.

```bash
git clone https://github.com/AliAdilQ/diabetes_risk_prediction.git
cd diabetes_risk_prediction
python -m venv venv
```

Activate on **Windows PowerShell**:

```powershell
.\venv\Scripts\Activate.ps1
```

Activate on **Windows Command Prompt**:

```bat
venv\Scripts\activate
```

Activate on **Linux/macOS**:

```bash
source venv/bin/activate
```

If `python` points to an older version, use `py -3.12` on Windows or `python3.12` on
Linux/macOS for virtual environment creation. Then, with the environment activated:

```bash
pip install -r requirements.txt
python scripts/generate_dummy_data.py
python scripts/train_model.py
python scripts/seed_database.py
python run.py
```

Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)**.

The CSV, trained pipeline, and metrics are already bundled. The generation and training
commands show the complete reproducible workflow and are safe to run again. The seed
script creates `instance/diabetes.db`, a local admin, and 24 sample predictions.
It checks unique seed keys and usernames, so repeating it creates no duplicate records
and does not reset an existing admin password.

## Configuration

Copy the example if you want persistent local sessions or custom settings.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

| Variable | Default / example | Behavior |
| --- | --- | --- |
| `SECRET_KEY` | `change-me` in example | Weak/missing values use a random ephemeral key locally. Production refuses weak keys. |
| `DATABASE_URL` | `sqlite:///diabetes.db` | Relative SQLite paths resolve inside `instance/`. |
| `FLASK_ENV` | `development` | `production` enables Secure cookies and requires a strong secret. This is an explicit app setting. |
| `FLASK_DEBUG` | `0` | Enable only while developing locally. |
| `RATELIMIT_STORAGE_URI` | `memory://` | Local per-process limiter storage; see deployment notes for shared limits. |

Generate a random secret with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Set that output as `SECRET_KEY` in your ignored `.env` file. A persistent key prevents
local sessions from being invalidated every time the app restarts. `.env`, virtual
environments, databases, and logs are excluded from Git.

## Demo Admin Login

| Field | Local demo value |
| --- | --- |
| URL | [http://127.0.0.1:5000/admin/login](http://127.0.0.1:5000/admin/login) |
| Username | `admin` |
| Email | `admin@example.com` |
| Password | `Admin@123` |

**These credentials are provided only for local demonstration. Change them before any public deployment.**

**These credentials are intended only for local demonstration. Change the password and secret key before deploying the application publicly.**

The password is hashed in the database. Sessions expire after 30 minutes of inactivity.
The admin is created only by the development seed script, never automatically by the web server.
Rotate a password using an interactive prompt:

```bash
flask --app run change-admin-password --username admin
```

## Try a prediction

1. Open `/predict` and select **Fill example**, or enter fictional measurements.
2. Submit the form. The server validates inputs and loads the trusted trained pipeline.
3. See the predicted class, estimated probability, model name, and entered values.
4. Sign into `/admin` to inspect the saved record and updated dashboard.

| Input | Example | Accepted demo range |
| --- | --- | --- |
| Pregnancies | 2 | 0–20, whole numbers |
| Glucose | 120 mg/dL | 40–250 |
| Diastolic blood pressure | 75 mm Hg | 30–150 |
| Triceps skin thickness | 25 mm | 0–100 |
| Insulin | 100 µU/mL | 0–900 |
| BMI | 26.5 kg/m² | 10–70 |
| Diabetes pedigree function | 0.45 | 0–3 |
| Age | 35 years | 18–100, whole numbers |

These are application validation limits, **not universal medical thresholds**. Zero
skin thickness or insulin means missing in this demo and is median-imputed. The
pedigree value is a dataset-specific score, not a substitute for a family-history assessment.
Use the example score to explore the app. The 50% class cutoff is a demo setting.

## Dataset and machine learning

`data/diabetes_sample.csv` contains **600 synthetic rows**, generated with seed 42.
No personal or clinical data was used. Values follow plausible-looking bounded
distributions, with a small number of zero missing-value sentinels. Labels are sampled
from an **invented probabilistic rule** using glucose, BMI, age, pedigree, and pregnancies.
This rule exists only to demonstrate supervised learning.

The feature schema resembles common Pima-style examples. **The bundled dataset is
synthetic/demo data and must NOT be treated as clinical data.** No real Pima dataset is
downloaded or included. Every record is fictional.

Recreate or enlarge the synthetic dataset:

```bash
python scripts/generate_dummy_data.py
python scripts/generate_dummy_data.py --rows 1000
python scripts/train_model.py
```

The training script:

1. Checks columns, converts values to numeric, removes duplicate rows and invalid targets.
2. Treats non-finite/negative measurements and invalid zeros as missing. Zero pregnancies
   and pedigree remain valid; the demo schema allows them.
3. Makes a stratified 80/20 training/test split with `random_state=42`.
4. Places median imputation inside each pipeline. Logistic Regression and KNN also
   use `StandardScaler` inside the pipeline.
5. Compares **Logistic Regression, Random Forest, Decision Tree, and K-Nearest Neighbors**
   with five stratified training folds. Preprocessing is fitted independently within each fold.
6. Selects the highest mean training-fold ROC-AUC; mean F1 breaks a tie. Test scores
   never determine the selected model.
7. Fits each pipeline on the training split and evaluates on the untouched test split.
8. Saves the selected fitted pipeline (including imputer/scaler) and provenance in
   `models/diabetes_model.pkl`, plus real metrics in `models/model_metrics.json`.

### Bundled model evaluation

Results from the included 600-row dataset; **480 training rows / 120 test rows**:

| Algorithm | Training CV ROC-AUC | Test accuracy | Test precision | Test recall | Test F1 | Test ROC-AUC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Logistic Regression — selected** | **0.8542** | 0.8167 | 0.8182 | 0.6279 | 0.7105 | 0.8771 |
| Random Forest | 0.8336 | 0.8250 | 0.8438 | 0.6279 | 0.7200 | 0.8725 |
| K-Nearest Neighbors | 0.8233 | 0.7583 | 0.7333 | 0.5116 | 0.6027 | 0.8321 |
| Decision Tree | 0.7654 | 0.8167 | 0.7561 | 0.7209 | 0.7381 | 0.8500 |

Selected model confusion matrix (rows = actual, columns = predicted; lower class first):

```text
              Predicted 0   Predicted 1
Actual 0          71             6
Actual 1          16            27
```

Accuracy measures correct class assignments; precision measures the correctness of
higher-class predictions; recall measures higher-class labels found; F1 balances precision
and recall. ROC-AUC measures class ranking across cutoffs. These describe **synthetic
labels only**, and the probability is not clinically calibrated.

The README table describes the bundled build. `/model-info` and `/admin/model-performance`
always read the current JSON report, so retraining updates the UI without editing templates.
The JSON includes per-model confusion matrices, CV variability, dataset SHA-256, package
versions, random state, and model version. Package version changes require retraining;
the application gives a useful message instead of loading an incompatible artifact.

## Web and JSON workflow

| Route | Purpose |
| --- | --- |
| `GET /` | Project home |
| `GET/POST /predict` | Validated form; successful POST saves and redirects |
| `GET /prediction-result` | Most recent result belonging to the submitting session |
| `GET /about` | Objective, stack, workflow, and limitations |
| `GET /model-info` | Live model report |
| `GET/POST /admin/login` | Administrator authentication |
| `GET /admin` | Protected dashboard |
| `GET /admin/predictions` | Search, filter, sort, and pagination |
| `GET /admin/predictions/<id>` | Protected individual record |
| `POST /admin/predictions/<id>/delete` | CSRF-protected deletion |
| `GET /admin/predictions/export` | Protected CSV export with current filters |
| `GET /admin/model-performance` | Protected ML evaluation |
| `POST /admin/logout` | CSRF-protected logout |
| `GET /api/csrf-token` | Establish session and fetch CSRF token |
| `POST /api/predict` | Validate JSON, estimate, and save |

Example JSON request:

```json
{
  "pregnancies": 2,
  "glucose": 120,
  "blood_pressure": 75,
  "skin_thickness": 25,
  "insulin": 100,
  "bmi": 26.5,
  "diabetes_pedigree": 0.45,
  "age": 35
}
```

From JavaScript on the app's origin (the session cookie accompanies both requests):

```javascript
const { csrf_token } = await fetch('/api/csrf-token').then(r => r.json());
const response = await fetch('/api/predict', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf_token },
  body: JSON.stringify({
    pregnancies: 2, glucose: 120, blood_pressure: 75, skin_thickness: 25,
    insulin: 100, bmi: 26.5, diabetes_pedigree: 0.45, age: 35
  })
});
console.log(response.status, await response.json());
```

Responses include `prediction` (`lower_risk` or `higher_risk`), numeric `probability`
in `[0, 1]`, model name, version, and `educational_only: true`. Returns **201** after
saving, **422** for invalid/missing/unknown inputs, **400** for malformed JSON or CSRF,
**415** for an incorrect content type, **429** for a rate limit, and **503** if the model
is unavailable. No CORS exemption or CSRF bypass is configured. For an external client,
keep the cookie from `/api/csrf-token` and send the returned token in `X-CSRFToken`.

## Architecture

```text
diabetes_risk_prediction/
├── app/
│   ├── __init__.py           # Factory, errors, security headers, CLI commands
│   ├── extensions.py         # Database, login, CSRF, request limiter
│   ├── features.py           # Shared feature schema and disclaimer
│   ├── models.py             # Admin and Prediction records
│   ├── forms.py              # Browser and API field validation
│   ├── routes.py             # Public pages and JSON prediction
│   ├── admin_routes.py       # Protected analytics and management
│   ├── ml_utils.py           # Artifact loading, inference, persistence
│   ├── templates/            # Public, admin, and error views
│   └── static/               # CSS, JS, favicon, licensed vendor assets
├── data/diabetes_sample.csv  # Fictional generated dataset
├── models/
│   ├── diabetes_model.pkl    # Trusted pipeline plus provenance
│   └── model_metrics.json    # Generated evaluation report
├── scripts/
│   ├── generate_dummy_data.py
│   ├── train_model.py
│   ├── seed_database.py
│   ├── capture_screenshots.cjs
│   ├── browser_wsgi_bridge.py
│   └── fetch_frontend_assets.py
├── screenshots/              # Five real application screenshots
├── tests/                    # Routes, validation, inference, authentication
├── .github/workflows/tests.yml
├── .env.example
├── .gitignore
├── config.py
├── run.py
├── pytest.ini
├── requirements.txt
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
├── THIRD_PARTY_NOTICES.md
└── LICENSE
```

At runtime Flask creates the ignored `instance/diabetes.db`. The factory separates
configuration from extensions and routes. Browser, API, and seed predictions share
the same preprocessing and inference path. Tests use isolated temporary databases.

## Testing and screenshots

```bash
python -m pytest -q
```

The completed build passed **88 pytest tests** and browser verification at **1440,
768, and 390px**, with no browser console errors or failed assets. The actual
screenshots are bundled above; the verification transport is documented below.

Tests cover public/error pages, input boundaries and non-finite values, saved predictions,
API contracts, result privacy, train-only imputation, admin access and password hashing,
CSRF on state changes, login throttling, filtering, pagination, export, deletion, logout,
production settings, CLI account management, and idempotent seeding. GitHub Actions
installs the pinned requirements, regenerates data, trains, and runs pytest on Linux.

To refresh screenshots, start the seeded app, install Playwright for Node separately
(only needed for this maintainer utility), and run in a second terminal:

```bash
npm install --no-save --package-lock=false playwright
npx playwright install chromium
node scripts/capture_screenshots.cjs
```

In an OS sandbox that prohibits loopback connections, set `FLASK_BRIDGE_PYTHON` to
the project's Python executable. The capture utility then sends browser requests
to the real Flask WSGI application over stdio; cookies, CSRF, templates, inference,
and database writes still run normally. The bundled screenshots were captured
using this fallback in headless Microsoft Edge. Network server startup was checked
separately. This fallback is only a local verification utility.

If using installed Microsoft Edge, set `PLAYWRIGHT_CHANNEL=msedge` instead of installing
Chromium. The script captures all five pages, submits a real prediction, checks charts,
filters, details, login/logout, console errors, failed resources, and overflow at 1440,
768, and 390 pixels. It adds one demonstration prediction to the local database.
It writes a verification report in ignored `.local/`. `SCREENSHOT_URL` can override
the default local origin. Vendor assets do not need regeneration during setup.

## Deployment and security

The source follows production-style patterns, but this application remains an
**educational demo**, not a clinical product. Before public deployment, review
[SECURITY.md](SECURITY.md), update dependencies as needed, set a strong secret and
`FLASK_ENV=production`, and use HTTPS. Deploy using a fresh database without the demo
account; do not run the demo seed script. Initialize tables and create an administrator:

```bash
flask --app run init-db
flask --app run create-admin
waitress-serve --listen=127.0.0.1:8000 run:app
```

The create-admin command prompts for a password of at least 12 characters. Waitress
works on Windows and Linux. Put it behind an HTTPS reverse proxy. Debug mode stays off
by default. Secure cookies in production require HTTPS.

The default limiter permits five login attempts/minute and thirty prediction
submissions/minute per connection IP. Its in-memory counters are local to a single
process and reset on restart. A public service needs shared/proxy rate limiting and
careful trusted-proxy configuration. Do not blindly trust forwarded IP headers.

SQLAlchemy parameterizes queries, Jinja escapes output, all POST actions use CSRF,
and sensitive pages use `no-store`. Predictions contain numeric inputs and no requested
personal identifiers; admins can inspect, export, or delete those records. Use fictional
inputs. Protect database backups and exports; no encryption-at-rest or compliance
system is provided. Only load trusted Joblib files.

### PostgreSQL later

The connection is configurable through `DATABASE_URL`. Install a PostgreSQL driver
(for example `psycopg[binary]`) when making that switch and use a URL such as
`postgresql+psycopg://user:password@host/database`. SQLAlchemy models and analytics are
portable; initialize a new database with `flask --app run init-db`. `create_all` creates
tables but does not upgrade existing schemas. Introduce a reviewed migration workflow
(such as Flask-Migrate/Alembic) before changing a deployed schema.

## Troubleshooting

| Issue | Fix |
| --- | --- |
| Python 3.8 or dependency install fails | Create the environment with Python 3.11 or 3.12. |
| No local database | Development startup creates tables; run the seed script for demo records. |
| Missing model or mismatched scikit-learn version | Run `python scripts/train_model.py`; restart the app if packages changed. |
| Missing dataset | Training regenerates it automatically, or run the generation script. |
| Empty metrics page | Retrain to recreate `models/model_metrics.json`. |
| Expired form / CSRF error | Refresh the form or fetch a fresh API token and preserve its cookie. |
| Login stops working after restarting locally | Configure a stable strong `SECRET_KEY` in `.env`. |
| Cookie/login issue with production settings locally | Production Secure cookies require HTTPS; use development settings for local HTTP. |
| Demo password no longer works | Existing passwords are never overwritten by seeding; use the password rotation CLI. |

## Limitations and medical disclaimer

Synthetic-data accuracy cannot be generalized to real populations. The invented rule,
limited schema, missing measurement context, and uncalibrated probabilities make this
unsuitable for screening, diagnosis, treatment, or individual medical decisions.
The application has no validated clinical thresholds or representative patient dataset.
If you have health concerns, speak with a qualified healthcare professional.

**This application is for educational and demonstration purposes only. It is not a medical diagnosis tool and should not replace professional medical advice.**

## Contributing, license, and author

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md), preserve educational
wording, and run the tests before submitting a pull request.

Licensed under the [MIT License](LICENSE). Third-party assets retain their own licenses;
see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

**Author:** [AliAdilQ](https://github.com/AliAdilQ) ·
**Repository:** [github.com/AliAdilQ/diabetes_risk_prediction](https://github.com/AliAdilQ/diabetes_risk_prediction)
