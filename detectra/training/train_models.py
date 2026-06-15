"""Train every model artifact required by the Detectra web application."""

import argparse
import sys
from pathlib import Path

import numpy as np

from detectra.analysis.pure import train_and_save_models
from detectra.paths import DATA_DIR, MODELS_DIR
from detectra.training.train_multi import train_multi_models


REFERENCE_SPECTRA = (
    "cocaine.csv",
    "heroin.csv",
    "methadone.csv",
    "morphine.csv",
    "meth.csv",
    "lactic.csv",
    "citric.csv",
    "ethanol.csv",
    "glucose.csv",
    "sucrose.csv",
)

MODEL_ARTIFACTS = (
    "drug_binary_xgb.pkl",
    "drug_multiclass_xgb.pkl",
    "drug_label_encoder.pkl",
    "ensemble_classifier_chains.pkl",
    "multidrug_label_binarizer.pkl",
)


def validate_training_inputs() -> None:
    """Fail early when a required reference spectrum is unavailable."""
    missing = [
        DATA_DIR / filename
        for filename in REFERENCE_SPECTRA
        if not (DATA_DIR / filename).is_file()
    ]
    if missing:
        formatted = "\n".join(f"  - {path}" for path in missing)
        raise FileNotFoundError(f"Missing reference spectra:\n{formatted}")


def print_artifact_status() -> None:
    """Display the model files expected by the web application."""
    print("\nExpected model artifacts:")
    for filename in MODEL_ARTIFACTS:
        path = MODELS_DIR / filename
        status = "ready" if path.is_file() else "missing"
        print(f"  [{status:7}] {path}")


def train_all_models() -> None:
    """Train pure-compound and multi-label models in sequence."""
    validate_training_inputs()
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    np.random.seed(42)

    print("Step 1/2: training pure-compound classifiers...")
    train_and_save_models()
    print("Pure-compound classifiers saved.")

    print("\nStep 2/2: training multi-label classifier chains...")
    print("This is the slower stage and may take several minutes.")
    train_multi_models()
    print("Multi-label classifier chains saved.")

    print_artifact_status()
    print("\nTraining complete. Start Detectra with: python app.py")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train all model artifacts required by Detectra."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate reference data and show artifact status without training.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        validate_training_inputs()
        if args.check:
            print("All required reference spectra are available.")
            print_artifact_status()
            return 0
        train_all_models()
        return 0
    except Exception as exc:
        print(f"\nTraining failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
