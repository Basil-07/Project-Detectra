"""Model artifact inventory and first-run status helpers."""

from collections.abc import Iterable

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


def missing_model_files(filenames: Iterable[str]) -> list[str]:
    """Return requested model artifact names that are unavailable locally."""
    return [
        filename
        for filename in filenames
        if not (MODELS_DIR / filename).is_file()
    ]
