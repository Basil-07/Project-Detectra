"""Focused tests for web-independent service helpers."""

import hashlib
from pathlib import Path
import zipfile

import pandas as pd

from detectra.services import model_artifacts
from detectra.services.validation import allowed_file, validate_csv_format


def test_allowed_file_accepts_csv_case_insensitively():
    assert allowed_file("sample.csv")
    assert allowed_file("sample.CSV")
    assert not allowed_file("sample.txt")


def test_validate_csv_format_accepts_minimum_valid_spectrum(tmp_path):
    filepath = tmp_path / "spectrum.csv"
    pd.DataFrame({
        "wavenumber": range(10),
        "absorbance": [0.1] * 10,
    }).to_csv(filepath, index=False)

    is_valid, message = validate_csv_format(filepath)

    assert is_valid
    assert message == "Valid CSV format"


def test_validate_csv_format_reports_missing_columns(tmp_path):
    filepath = tmp_path / "invalid.csv"
    pd.DataFrame({"value": range(10)}).to_csv(filepath, index=False)

    is_valid, message = validate_csv_format(filepath)

    assert not is_valid
    assert "wavenumber" in message
    assert "absorbance" in message


def test_missing_model_files_uses_configured_models_directory(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(model_artifacts, "MODELS_DIR", Path(tmp_path))
    (tmp_path / "present.pkl").write_bytes(b"model")

    missing = model_artifacts.missing_model_files(
        ("present.pkl", "missing.pkl")
    )

    assert missing == ["missing.pkl"]


def test_ensure_model_files_downloads_and_verifies_archive(
    tmp_path,
    monkeypatch,
):
    source_directory = tmp_path / "source"
    source_directory.mkdir()
    archive_path = source_directory / "models.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("required.pkl", b"model")

    checksum = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    destination = tmp_path / "runtime-models"
    monkeypatch.setattr(model_artifacts, "MODELS_DIR", destination)
    monkeypatch.setenv(
        model_artifacts.MODEL_ARCHIVE_URL_VARIABLE,
        archive_path.resolve().as_uri(),
    )
    monkeypatch.setenv(
        model_artifacts.MODEL_ARCHIVE_SHA_VARIABLE,
        checksum,
    )

    model_artifacts.ensure_model_files(("required.pkl",))

    assert (destination / "required.pkl").read_bytes() == b"model"
