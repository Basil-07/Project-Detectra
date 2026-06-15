"""Package locally trained model artifacts for a GitHub Release."""

import argparse
import hashlib
import zipfile
from pathlib import Path

import joblib

from detectra.paths import MODELS_DIR, PROJECT_ROOT
from detectra.training.train_models import MODEL_ARTIFACTS


def package_models(output_path: Path) -> Path:
    """Create a compressed archive containing every required model artifact."""
    missing = [
        MODELS_DIR / filename
        for filename in MODEL_ARTIFACTS
        if not (MODELS_DIR / filename).is_file()
    ]
    if missing:
        formatted = "\n".join(f"  - {path}" for path in missing)
        raise FileNotFoundError(f"Missing model artifacts:\n{formatted}")

    _validate_deployment_ensemble()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for filename in MODEL_ARTIFACTS:
            archive.write(MODELS_DIR / filename, arcname=filename)
    return output_path


def _validate_deployment_ensemble() -> None:
    """Reject legacy ensembles that still require the oversized CatBoost wheel."""
    chains = joblib.load(MODELS_DIR / "ensemble_classifier_chains.pkl")
    if len(chains) != 5:
        raise ValueError(
            "The Vercel ensemble must contain exactly five classifier chains. "
            "Retrain with `python -m detectra.training.train_models`."
        )
    for chain in chains:
        estimator = getattr(chain, "estimator", None)
        if estimator is None:
            estimator = getattr(chain, "base_estimator", None)
        module_name = type(estimator).__module__ if estimator is not None else ""
        if module_name.startswith("catboost"):
            raise ValueError(
                "The ensemble still contains CatBoost and is too large for "
                "Vercel. Retrain with "
                "`python -m detectra.training.train_models` before packaging."
            )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create the model archive used by Vercel deployments."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "dist" / "detectra-models.zip",
    )
    args = parser.parse_args()
    archive = package_models(args.output)
    print(f"Created: {archive}")
    print(f"SHA256:  {sha256(archive)}")


if __name__ == "__main__":
    main()
