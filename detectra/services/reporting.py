"""Dependency-free PDF report generation for completed analyses."""

from datetime import datetime
from pathlib import Path


def generate_pdf_report(
    result_data: dict,
    reports_folder: str | Path,
    report_type: str = "pure",
    filename: str | None = None,
    plot_image_path: str | Path | None = None,
) -> Path:
    """Generate a compact text PDF report and return its filesystem path."""
    del plot_image_path
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"detectra_report_{report_type}_{timestamp}.pdf"

    filepath = Path(reports_folder) / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "Detectra IR Spectrum Analysis Report",
        "",
        f"Report Type: {report_type.title()} Compound Analysis",
        f"Generated: {datetime.now():%Y-%m-%d %H:%M:%S}",
        "",
        "Analysis Results",
        *_result_summary(result_data, report_type),
    ]
    lines.extend(_detected_peaks(result_data))
    filepath.write_bytes(_build_pdf(lines))
    return filepath


def _result_summary(result_data: dict, report_type: str) -> list[str]:
    if report_type == "pure":
        if result_data.get("is_drug"):
            return [
                f'Drug Detected: {result_data.get("drug_type", "Unknown").title()}',
                f'Confidence: {result_data.get("confidence", 0) * 100:.1f}%',
            ]
        return [
            "No drug compound detected",
            f'Drug Probability: {result_data.get("probability", 0) * 100:.1f}%',
        ]

    if report_type == "mixture":
        return [
            f'Dominant Compound: {result_data.get("dominant_compound", "None")}',
            (
                "Peak Matching: "
                f'{result_data.get("peak_matching_percentage", 0):.1f}%'
            ),
        ]

    if report_type == "multiple":
        detected = result_data.get("detected_drugs", [])
        summary = ", ".join(detected) if detected else "No drug compounds detected"
        return [f"Detected Drugs: {summary}"]

    return ["No report summary is available."]


def _detected_peaks(result_data: dict) -> list[str]:
    peaks = result_data.get("detected_peaks", [])
    if not peaks:
        return []
    return [
        "",
        "Detected Peaks (cm^-1)",
        *(f"{index}. {peak:.1f} cm^-1" for index, peak in enumerate(peaks[:10], 1)),
    ]


def _pdf_text(value: str) -> str:
    ascii_value = value.encode("ascii", errors="replace").decode("ascii")
    return ascii_value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_pdf(lines: list[str]) -> bytes:
    content_lines = ["BT", "/F1 16 Tf", "50 790 Td"]
    for index, line in enumerate(lines):
        if index:
            content_lines.append("0 -22 Td")
        if index == 5:
            content_lines.append("/F1 14 Tf")
        elif index == 6:
            content_lines.append("/F1 11 Tf")
        content_lines.append(f"({_pdf_text(line)}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("ascii")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R "
            b"/MediaBox [0 0 612 842] "
            b"/Resources << /Font << /F1 4 0 R >> >> "
            b"/Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        (
            f"<< /Length {len(stream)} >>\nstream\n".encode("ascii")
            + stream
            + b"\nendstream"
        ),
    ]

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, object_data in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode("ascii"))
        output.extend(object_data)
        output.extend(b"\nendobj\n")

    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(output)
