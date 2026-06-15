# Detectra

Detectra is a Flask application for machine-learning-assisted infrared (IR)
spectrum analysis. It supports pure-compound classification, synthetic
drug/cutting-agent mixture simulation, and multi-label analysis of combined
reference spectra.

> Detectra is a research and educational prototype. Its predictions are not
> validated for clinical, legal, or forensic decision-making.

## Features

- Upload a CSV spectrum and classify it as drug or non-drug.
- Identify cocaine, heroin, methadone, morphine, or methamphetamine.
- Generate synthetic two-component spectra at configurable concentrations.
- Detect multiple drug labels with an ensemble of classifier chains.
- Render spectrum plots and downloadable PDF reports.

## Repository Layout

```text
detectra/
  analysis/          Spectrum processing and inference algorithms
  services/          Validation, plotting, reporting, and model inventory
  training/          Offline model-training commands
  templates/         Flask/Jinja pages
  static/            Version-controlled frontend assets
  config.py          Application configuration
  paths.py           Canonical project paths
  routes.py          Flask routes and request orchestration
  web.py             Flask application assembly
data/
  reference_spectra/ Input spectra used by training and simulations
models/               Locally generated model artifacts (ignored by Git)
tests/                Automated smoke tests and model evaluation utilities
docs/                 Architecture and development documentation
instance/             Ignored uploads, reports, plots, and local outputs
app.py                Local development entry point
```

## Requirements

- Python 3.11
- A virtual environment is strongly recommended

Model artifacts are intentionally not committed to Git. A fresh clone must
train them locally with the pinned runtime before using pure or multi-compound
analysis.

## Setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Set `DETECTRA_SECRET_KEY` in `.env` or in the process environment before any
shared or deployed use.

## First Run and Model Training

Follow the complete [first-run walkthrough](docs/FIRST_RUN.md). The short
version is:

```powershell
python -m detectra.training.train_models --check
python -m detectra.training.train_models
python app.py
```

Training creates all five required `.pkl` artifacts under `models/`. They remain
local because `models/*.pkl` is excluded by `.gitignore`.

## Run

```powershell
python app.py
```

Open `http://127.0.0.1:5000`.

Flask CLI usage is also supported:

```powershell
flask --app app run --debug
```

## Spectrum CSV Format

Input files must contain at least ten rows and these columns:

```csv
wavenumber,absorbance
4000.0,0.012
3999.0,0.014
```

Extra columns are allowed.

## Quality Checks

```powershell
pytest
ruff check .
```

The exhaustive synthetic multi-label evaluation is intentionally separate
from the fast test suite:

```powershell
python -m tests.evaluate_multi_model
```

Its output is written to `instance/multi_model_evaluation.csv`.

## Training

Train or retrain every required model:

```powershell
python -m detectra.training.train_models
```

Individual training entry points remain available for development, but the
combined command is the supported first-run workflow.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the processing flow and
[CONTRIBUTING.md](CONTRIBUTING.md) for development conventions.

