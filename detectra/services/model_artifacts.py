"""Model artifact inventory and first-run status helpers."""

import hashlib
import os
import shutil
import tempfile
import urllib.request
import zipfile
from collections.abc import Iterable
from pathlib import Path

from detectra.paths import MODELS_DIR


PURE_MODEL_FILES = (
    "drug_binary_xgb.pkl",
    "drug_multiclass_xgb.pkl",
    "drug_label_encoder.pkl",
)
MULTI_MODEL_FILES = (
    "ensemble_classifier_chains.pkl",
    "multidrug_label_binarizer.pkl",
)
TRAINING_COMMAND = "python -m detectra.training.train_models"
MODEL_ARCHIVE_URL_VARIABLE = "DETECTRA_MODELS_URL"
MODEL_ARCHIVE_SHA_VARIABLE = "DETECTRA_MODELS_SHA256"


def missing_model_files(filenames: Iterable[str]) -> list[str]:
    """Return requested model artifact names that are unavailable locally."""
    return [
        filename
        for filename in filenames
        if not (MODELS_DIR / filename).is_file()
    ]


def models_can_be_prepared(filenames: Iterable[str]) -> bool:
    """Return whether models exist or a remote archive is configured."""
    return not missing_model_files(filenames) or bool(
        os.getenv(MODEL_ARCHIVE_URL_VARIABLE)
    )


def ensure_model_files(filenames: Iterable[str]) -> None:
    """Download and safely extract the configured model archive when needed."""
    filenames = tuple(filenames)
    if not missing_model_files(filenames):
        return

    archive_url = os.getenv(MODEL_ARCHIVE_URL_VARIABLE)
    if not archive_url:
        missing = ", ".join(missing_model_files(filenames))
        raise FileNotFoundError(
            f"Missing model artifacts: {missing}. Run `{TRAINING_COMMAND}` "
            f"or configure {MODEL_ARCHIVE_URL_VARIABLE}."
        )

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary_directory:
        archive_path = Path(temporary_directory) / "detectra-models.zip"
        with urllib.request.urlopen(archive_url, timeout=120) as response:
            with archive_path.open("wb") as archive_file:
                shutil.copyfileobj(response, archive_file)

        expected_sha = os.getenv(MODEL_ARCHIVE_SHA_VARIABLE, "").lower()
        if expected_sha:
            actual_sha = _sha256(archive_path)
            if actual_sha != expected_sha:
                raise ValueError(
                    "Downloaded model archive checksum does not match "
                    f"{MODEL_ARCHIVE_SHA_VARIABLE}."
                )

        _safe_extract_archive(archive_path, MODELS_DIR)

    missing = missing_model_files(filenames)
    if missing:
        raise FileNotFoundError(
            "Model archive did not contain required files: "
            + ", ".join(missing)
        )


def _safe_extract_archive(archive_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            member_path = Path(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError("Model archive contains an unsafe path.")
            if member.is_dir():
                continue
            target = destination / member_path.name
            with archive.open(member) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
