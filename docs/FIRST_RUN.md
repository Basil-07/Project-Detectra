# First-Run Walkthrough

This guide starts from a fresh clone of Detectra. Trained `.pkl` model files are
not stored in Git, so every new installation must train them locally before the
analysis features can be used.

## 1. Prerequisites

- Git
- Python 3.12
- At least several gigabytes of free memory
- A few minutes for dependency installation and model training

Confirm the Python version:

```text
python --version
```

It should report Python 3.12.x. On Windows, `py -3.12 --version` may be more
reliable.

## 2. Clone the Repository

```text
git clone <repository-url>
cd detectra
```

Replace `<repository-url>` with the GitHub clone URL.

## 3. Create a Virtual Environment

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### macOS or Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

## 4. Install Dependencies

```text
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Contributors should use `requirements-dev.txt` instead.

## 5. Configure the Application

Copy the example environment file.

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### macOS or Linux

```bash
cp .env.example .env
```

Replace `DETECTRA_SECRET_KEY` in `.env` with a long random value before sharing
or deploying the application.

## 6. Check the Training Inputs

```text
python -m detectra.training.train_models --check
```

This verifies the ten reference spectra in `data/reference_spectra/` and shows
which model artifacts are missing.

## 7. Train All Models

```text
python -m detectra.training.train_models
```

The command performs two stages:

1. Trains the binary drug detector and pure-drug classifier.
2. Trains the multi-label ensemble of classifier chains.

The second stage is slower. Keep the terminal open until the command prints
`Training complete`.

Five generated files will appear under `models/`:

```text
drug_binary_xgb.pkl
drug_multiclass_xgb.pkl
drug_label_encoder.pkl
ensemble_classifier_chains.pkl
multidrug_label_binarizer.pkl
```

These files are intentionally ignored by Git. Do not commit them.

## 8. Start Detectra

```text
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in a browser.

## 9. Confirm the Installation

1. Open **Pure Analysis**.
2. Upload `data/reference_spectra/cocaine.csv`.
3. Confirm that an analysis result and spectrum plot appear.
4. Open **Multiple Compounds** and test a simple combination.

## Common Problems

### A model file is missing

Run:

```text
python -m detectra.training.train_models --check
python -m detectra.training.train_models
```

Make sure the command is executed from the repository root with the virtual
environment active.

### A serialized-model version warning appears

Delete locally generated `.pkl` files and retrain them inside the current
virtual environment. Do not copy model artifacts between incompatible
scikit-learn or XGBoost environments.

### Training stops because a package is missing

Reactivate the virtual environment and reinstall:

```text
python -m pip install -r requirements.txt
```

### The web server starts but analysis fails

Check that all five files listed above exist in `models/`. Mixture simulation
can render without trained models, but pure and multi-compound analysis require
their corresponding artifacts.
