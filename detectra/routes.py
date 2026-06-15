"""HTTP routes and request orchestration for Detectra."""

from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from flask import (
    flash,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from detectra.analysis.mixture import (
    DRUGS,
    find_characteristic_peaks,
    generate_mixture,
    wavenumbers,
)
from detectra.analysis.multi import (
    COMMON_AXIS,
    compound_files,
    load_and_interpolate_spectrum,
)
from detectra.analysis.pure import predict_sample
from detectra.paths import DATA_DIR, MODELS_DIR
from detectra.services.model_artifacts import (
    MULTI_MODEL_FILES,
    PURE_MODEL_FILES,
    TRAINING_COMMAND,
    missing_model_files,
)
from detectra.services.plotting import create_overlaid_plot, create_spectrum_plot
from detectra.services.reporting import generate_pdf_report
from detectra.services.validation import allowed_file, validate_csv_format


def register_routes(app) -> None:
    """Register all public routes and error handlers on a Flask app."""

    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/plots/<path:filename>")
    def generated_plot(filename):
        return send_from_directory(app.config["PLOTS_FOLDER"], filename)

    @app.route("/upload", methods=["GET", "POST"])
    def upload():
        if request.method == "POST":
            missing_models = missing_model_files(PURE_MODEL_FILES)
            if missing_models:
                _flash_training_required("Pure-analysis")
                return redirect(request.url)

            upload_file = request.files.get("file")
            if upload_file is None or upload_file.filename == "":
                flash("No file selected", "error")
                return redirect(request.url)
            if not allowed_file(upload_file.filename):
                flash("Only CSV files are allowed", "error")
                return redirect(request.url)

            timestamp = _timestamp()
            filename = f"{timestamp}_{secure_filename(upload_file.filename)}"
            filepath = Path(app.config["UPLOAD_FOLDER"]) / filename
            try:
                upload_file.save(filepath)
                is_valid, message = validate_csv_format(filepath)
                if not is_valid:
                    flash(message, "error")
                    return redirect(request.url)

                result = _predict_pure_sample(filepath)
                dataframe = pd.read_csv(filepath)
                plot_filename = f"spectrum_{timestamp}.png"
                plot_path = Path(app.config["PLOTS_FOLDER"]) / plot_filename
                create_spectrum_plot(
                    dataframe,
                    "IR Spectrum Analysis",
                    result.get("detected_peaks", []),
                    plot_path,
                )

                result.update({
                    "spectrum_plot": url_for(
                        "generated_plot",
                        filename=plot_filename,
                    ),
                    "_plot_path": str(plot_path),
                    "sample_name": request.form.get(
                        "sample_name",
                        "Unknown Sample",
                    ),
                    "notes": request.form.get("notes", ""),
                })
                session["last_pure_analysis_result"] = result
                return render_template("output.html", result=result)
            except Exception as exc:
                flash(f"Error processing file: {exc}", "error")
                return redirect(request.url)
            finally:
                filepath.unlink(missing_ok=True)

        return render_template(
            "upload.html",
            models_ready=not missing_model_files(PURE_MODEL_FILES),
            training_command=TRAINING_COMMAND,
        )

    @app.route("/mixture", methods=["GET", "POST"])
    def mixture():
        if request.method == "POST":
            try:
                drug = request.form.get("drug")
                drug_percentage = float(request.form.get("drug_percentage", 50))
                cutting_agent = request.form.get("cutting_agent")
                cutting_percentage = float(
                    request.form.get("cutting_percentage", 50)
                )
                notes = request.form.get("notes", "")

                if drug_percentage + cutting_percentage != 100:
                    flash("Percentages must total 100%", "error")
                    return redirect(request.url)

                mixture_spectrum = generate_mixture(
                    drug,
                    drug_percentage,
                    cutting_agent,
                    cutting_percentage,
                )
                mixture_dataframe = pd.DataFrame({
                    "wavenumber": wavenumbers,
                    "absorbance": mixture_spectrum,
                })
                found_peaks = find_characteristic_peaks(mixture_spectrum, drug)
                matching_percentage = len(found_peaks) / len(DRUGS[drug]) * 100
                pure_dataframe = pd.read_csv(DATA_DIR / f"{drug}.csv")

                timestamp = _timestamp()
                mixture_filename = f"mixture_{timestamp}.png"
                pure_filename = f"pure_{timestamp}.png"
                mixture_plot_path = (
                    Path(app.config["PLOTS_FOLDER"]) / mixture_filename
                )
                pure_plot_path = Path(app.config["PLOTS_FOLDER"]) / pure_filename

                create_spectrum_plot(
                    mixture_dataframe,
                    f"{drug.title()} Mixture Spectrum",
                    save_path=mixture_plot_path,
                )
                create_spectrum_plot(
                    pure_dataframe,
                    f"Pure {drug.title()} Reference",
                    save_path=pure_plot_path,
                )

                results = {
                    "dominant_compound": (
                        drug if matching_percentage > 50 else None
                    ),
                    "peak_matching_percentage": matching_percentage,
                    "mixture_spectrum_plot": url_for(
                        "generated_plot",
                        filename=mixture_filename,
                    ),
                    "pure_spectrum_plot": url_for(
                        "generated_plot",
                        filename=pure_filename,
                    ),
                    "_plot_path": str(mixture_plot_path),
                    "peak_comparison": [
                        {
                            "expected": peak[0],
                            "mixture": peak[1],
                            "pure": peak[0],
                            "intensity_ratio": peak[2],
                            "match_status": (
                                "good"
                                if abs(peak[0] - peak[1]) < 15
                                else "partial"
                            ),
                        }
                        for peak in found_peaks
                    ],
                    "analysis_notes": (
                        f"Generated mixture with {drug_percentage}% {drug} "
                        f"and {cutting_percentage}% {cutting_agent}"
                    ),
                }
                mixture_config = {
                    "drug": drug,
                    "drug_percentage": drug_percentage,
                    "cutting_agent": cutting_agent,
                    "cutting_percentage": cutting_percentage,
                    "notes": notes,
                }
                session["last_mixture_analysis_results"] = results
                return render_template(
                    "mixture_output.html",
                    results=results,
                    mixture_config=mixture_config,
                )
            except Exception as exc:
                flash(f"Error generating mixture: {exc}", "error")
                return redirect(request.url)

        return render_template("mixture.html")

    @app.route("/multiple", methods=["GET", "POST"])
    def multiple():
        if request.method == "POST":
            missing_models = missing_model_files(MULTI_MODEL_FILES)
            if missing_models:
                _flash_training_required("Multi-compound")
                return redirect(request.url)

            selected_drugs = request.form.getlist("drugs")
            selected_non_drugs = request.form.getlist("non_drugs")
            validation_error = _validate_compound_selection(
                selected_drugs,
                selected_non_drugs,
            )
            if validation_error:
                flash(validation_error, "error")
                return redirect(request.url)

            try:
                results = _analyze_multiple_compounds(
                    selected_drugs + selected_non_drugs,
                    app.config["PLOTS_FOLDER"],
                )
                session["last_multi_analysis_results"] = results
                return render_template(
                    "multi_output.html",
                    results=results,
                    input_compounds={
                        "drugs": selected_drugs,
                        "non_drugs": selected_non_drugs,
                        "notes": request.form.get("notes", ""),
                    },
                )
            except Exception as exc:
                flash(f"Error processing multiple compounds: {exc}", "error")
                return redirect(request.url)

        return render_template(
            "multiple.html",
            models_ready=not missing_model_files(MULTI_MODEL_FILES),
            training_command=TRAINING_COMMAND,
        )

    @app.route("/download_report")
    def download_report():
        return _download_report(
            app,
            "last_pure_analysis_result",
            "pure",
            "No analysis data found to generate report.",
        )

    @app.route("/download_mixture_report")
    def download_mixture_report():
        return _download_report(
            app,
            "last_mixture_analysis_results",
            "mixture",
            "No mixture analysis data found to generate report.",
        )

    @app.route("/download_multi_report")
    def download_multi_report():
        return _download_report(
            app,
            "last_multi_analysis_results",
            "multiple",
            "No multi-compound analysis data found to generate report.",
        )

    @app.errorhandler(404)
    def not_found_error(_error):
        return render_template("home.html"), 404

    @app.errorhandler(500)
    def internal_error(_error):
        return render_template("home.html"), 500


def _predict_pure_sample(filepath: Path) -> dict:
    binary_model = joblib.load(MODELS_DIR / "drug_binary_xgb.pkl")
    multiclass_model = joblib.load(MODELS_DIR / "drug_multiclass_xgb.pkl")
    label_encoder = joblib.load(MODELS_DIR / "drug_label_encoder.pkl")
    result = predict_sample(
        filepath,
        binary_model,
        multiclass_model,
        label_encoder,
    )
    if result.get("error"):
        raise ValueError(result["error"])
    return result


def _validate_compound_selection(
    selected_drugs: list[str],
    selected_non_drugs: list[str],
) -> str | None:
    if len(selected_drugs) > 2:
        return "Maximum 2 drug compounds allowed"
    if len(selected_non_drugs) > 5:
        return "Maximum 5 non-drug compounds allowed"
    if not selected_drugs and not selected_non_drugs:
        return "Please select at least one compound"
    return None


def _analyze_multiple_compounds(
    selected_compounds: list[str],
    plots_folder: str,
) -> dict:
    chains = joblib.load(MODELS_DIR / "ensemble_classifier_chains.pkl")
    label_binarizer = joblib.load(
        MODELS_DIR / "multidrug_label_binarizer.pkl"
    )

    mixture = np.zeros_like(COMMON_AXIS)
    for compound in selected_compounds:
        mixture += load_and_interpolate_spectrum(compound_files[compound])
    mixture /= len(selected_compounds)

    mixture_input = mixture.reshape(1, -1)
    predictions = np.array([
        chain.predict(mixture_input)[0] for chain in chains
    ])
    vote_fraction = np.mean(predictions, axis=0)
    ensemble_prediction = (vote_fraction >= 0.5).astype(int)
    detected_drugs = list(
        label_binarizer.inverse_transform(
            ensemble_prediction.reshape(1, -1)
        )[0]
    )

    spectra_data = {"Mixture": mixture}
    for drug in detected_drugs:
        spectra_data[f"{drug.title()} Reference"] = (
            load_and_interpolate_spectrum(compound_files[drug])
        )

    timestamp = _timestamp()
    plot_filename = f"multi_{timestamp}.png"
    plot_path = Path(plots_folder) / plot_filename
    create_overlaid_plot(spectra_data, plot_path)

    model_names = (
        "XGBoost",
        "Extra Trees",
        "Ridge",
        "CatBoost",
        "Support Vector Classifier",
        "AdaBoost",
    )
    model_performance = []
    for name, prediction in zip(model_names, predictions):
        predicted_labels = list(
            label_binarizer.inverse_transform(
                prediction.reshape(1, -1)
            )[0]
        )
        agreement = float(np.mean(prediction == ensemble_prediction) * 100)
        model_performance.append({
            "name": name,
            "prediction": predicted_labels,
            "confidence": agreement,
            "status": "good" if agreement >= 80 else "partial",
        })

    return {
        "detected_drugs": detected_drugs,
        "overlaid_spectrum_plot": url_for(
            "generated_plot",
            filename=plot_filename,
        ),
        "_plot_path": str(plot_path),
        "prediction_confidence": {
            drug: float(
                vote_fraction[list(label_binarizer.classes_).index(drug)] * 100
            )
            for drug in detected_drugs
        },
        "spectrum_legend": [
            {"label": label, "color": color}
            for label, color in zip(
                spectra_data,
                ("blue", "red", "green", "orange", "purple", "brown", "pink"),
            )
        ],
        "model_performance": model_performance,
        "peak_analysis": {},
    }


def _download_report(app, session_key, report_type, missing_message):
    result_data = session.get(session_key)
    if not result_data:
        flash(missing_message, "error")
        return redirect(url_for("home"))

    try:
        filepath = generate_pdf_report(
            result_data,
            app.config["REPORTS_FOLDER"],
            report_type,
            plot_image_path=result_data.get("_plot_path"),
        )
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filepath.name,
        )
    except Exception as exc:
        flash(f"Error generating report: {exc}", "error")
        return redirect(url_for("home"))


def _flash_training_required(analysis_name: str) -> None:
    flash(
        f"{analysis_name} models are not trained. Run "
        f"`{TRAINING_COMMAND}` from the repository root.",
        "error",
    )


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
