"""PDF report generation for completed analyses."""

from datetime import datetime
from pathlib import Path

from fpdf import FPDF
from PIL import Image


def generate_pdf_report(
    result_data: dict,
    reports_folder: str | Path,
    report_type: str = "pure",
    filename: str | None = None,
    plot_image_path: str | Path | None = None,
) -> Path:
    """Generate a PDF report and return its filesystem path."""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"detectra_report_{report_type}_{timestamp}.pdf"

    filepath = Path(reports_folder) / filename
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Detectra IR Spectrum Analysis Report", 0, 1, "C")
    pdf.ln(10)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Report Type: {report_type.title()} Compound Analysis", 0, 1)
    pdf.cell(0, 10, f"Generated: {datetime.now():%Y-%m-%d %H:%M:%S}", 0, 1)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Analysis Results", 0, 1)
    pdf.set_font("Arial", "", 12)
    _write_result_summary(pdf, result_data, report_type)
    _write_detected_peaks(pdf, result_data)
    _embed_plot(pdf, plot_image_path)

    pdf.output(str(filepath))
    return filepath


def _write_result_summary(pdf: FPDF, result_data: dict, report_type: str) -> None:
    if report_type == "pure":
        if result_data.get("is_drug"):
            drug = result_data.get("drug_type", "Unknown").title()
            pdf.cell(0, 10, f"Drug Detected: {drug}", 0, 1)
            pdf.cell(
                0,
                10,
                f'Confidence: {result_data.get("confidence", 0) * 100:.1f}%',
                0,
                1,
            )
        else:
            pdf.cell(0, 10, "No drug compound detected", 0, 1)
            pdf.cell(
                0,
                10,
                f'Drug Probability: {result_data.get("probability", 0) * 100:.1f}%',
                0,
                1,
            )
    elif report_type == "mixture":
        dominant = result_data.get("dominant_compound", "None")
        matching = result_data.get("peak_matching_percentage", 0)
        pdf.cell(0, 10, f"Dominant Compound: {dominant}", 0, 1)
        pdf.cell(0, 10, f"Peak Matching: {matching:.1f}%", 0, 1)
    elif report_type == "multiple":
        detected = result_data.get("detected_drugs", [])
        summary = ", ".join(detected) if detected else "No drug compounds detected"
        pdf.cell(0, 10, f"Detected Drugs: {summary}", 0, 1)


def _write_detected_peaks(pdf: FPDF, result_data: dict) -> None:
    if "detected_peaks" not in result_data:
        return

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Detected Peaks (cm^-1)", 0, 1)
    pdf.set_font("Arial", "", 10)
    for index, peak in enumerate(result_data["detected_peaks"][:10], 1):
        pdf.cell(0, 8, f"{index}. {peak:.1f} cm^-1", 0, 1)


def _embed_plot(pdf: FPDF, plot_image_path: str | Path | None) -> None:
    if not plot_image_path:
        return

    path = Path(plot_image_path)
    if not path.is_file():
        return

    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "IR Spectrum Plot", 0, 1)
    pdf.ln(2)

    if path.suffix.lower() == ".svg":
        pdf.image(str(path), x=15, y=pdf.get_y(), w=180)
        return

    with Image.open(path) as image:
        width, height = image.size
        pdf_width = 180
        pdf_height = pdf_width * height / width
        if pdf_height > pdf.h - pdf.get_y() - 20:
            pdf.add_page()
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "IR Spectrum Plot (Continued)", 0, 1)
            pdf.ln(2)
        pdf.image(str(path), x=15, y=pdf.get_y(), w=pdf_width)
