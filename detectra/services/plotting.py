"""Lightweight SVG rendering helpers for spectrum visualizations."""

import base64
from html import escape
from pathlib import Path

import numpy as np

from detectra.analysis.multi import COMMON_AXIS


PLOT_COLORS = ("#2569ad", "#d14f5b", "#258f72", "#d9822b", "#7656b4", "#8a6642")
SVG_WIDTH = 1200
SVG_HEIGHT = 700


def _finish_plot(svg: str, save_path: str | Path | None) -> str:
    if save_path:
        Path(save_path).write_text(svg, encoding="utf-8")
        return str(save_path)

    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _normalize_series(series: list[tuple[str, np.ndarray, np.ndarray]]) -> tuple:
    finite_series = []
    all_x = []
    all_y = []
    for label, x_values, y_values in series:
        x_array = np.asarray(x_values, dtype=float)
        y_array = np.asarray(y_values, dtype=float)
        finite = np.isfinite(x_array) & np.isfinite(y_array)
        x_array = x_array[finite]
        y_array = y_array[finite]
        if not len(x_array):
            continue
        finite_series.append((label, x_array, y_array))
        all_x.extend(x_array)
        all_y.extend(y_array)

    if not finite_series:
        raise ValueError("No finite spectrum data is available to plot.")

    return finite_series, min(all_x), max(all_x), min(all_y), max(all_y)


def _render_svg(
    series: list[tuple[str, np.ndarray, np.ndarray]],
    title: str,
    markers: list[tuple[float, float]] | None = None,
) -> str:
    series, x_min, x_max, y_min, y_max = _normalize_series(series)
    left, right, top, bottom = 95, 40, 75, 85
    plot_width = SVG_WIDTH - left - right
    plot_height = SVG_HEIGHT - top - bottom
    x_span = x_max - x_min or 1
    y_span = y_max - y_min or 1
    y_padding = y_span * 0.08
    y_min -= y_padding
    y_max += y_padding
    y_span = y_max - y_min or 1

    def sx(value: float) -> float:
        return left + (x_max - value) / x_span * plot_width

    def sy(value: float) -> float:
        return top + (y_max - value) / y_span * plot_height

    elements = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" '
            f'height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">'
        ),
        "<style>"
        ".title{font:700 26px Arial,sans-serif;fill:#173b63}"
        ".label{font:16px Arial,sans-serif;fill:#315575}"
        ".tick{font:13px Arial,sans-serif;fill:#58738c}"
        ".legend{font:14px Arial,sans-serif;fill:#294d6d}"
        "</style>",
        '<rect width="100%" height="100%" rx="16" fill="#f8fbff"/>',
        (
            f'<text class="title" x="{SVG_WIDTH / 2}" y="40" '
            f'text-anchor="middle">{escape(title)}</text>'
        ),
    ]

    for index in range(6):
        fraction = index / 5
        x = left + fraction * plot_width
        y = top + fraction * plot_height
        x_value = x_max - fraction * x_span
        y_value = y_max - fraction * y_span
        elements.extend([
            (
                f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" '
                f'y2="{top + plot_height}" stroke="#dbe8f4"/>'
            ),
            (
                f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" '
                f'y2="{y:.1f}" stroke="#dbe8f4"/>'
            ),
            (
                f'<text class="tick" x="{x:.1f}" y="{top + plot_height + 24}" '
                f'text-anchor="middle">{x_value:.0f}</text>'
            ),
            (
                f'<text class="tick" x="{left - 12}" y="{y + 5:.1f}" '
                f'text-anchor="end">{y_value:.3g}</text>'
            ),
        ])

    elements.extend([
        (
            f'<line x1="{left}" y1="{top + plot_height}" '
            f'x2="{left + plot_width}" y2="{top + plot_height}" '
            'stroke="#6d8aa4" stroke-width="2"/>'
        ),
        (
            f'<line x1="{left}" y1="{top}" x2="{left}" '
            f'y2="{top + plot_height}" stroke="#6d8aa4" stroke-width="2"/>'
        ),
    ])

    for index, (label, x_values, y_values) in enumerate(series):
        step = max(1, len(x_values) // 1200)
        points = " ".join(
            f"{sx(x):.1f},{sy(y):.1f}"
            for x, y in zip(x_values[::step], y_values[::step])
        )
        color = PLOT_COLORS[index % len(PLOT_COLORS)]
        elements.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" '
            'stroke-width="2.5" stroke-linejoin="round"/>'
        )
        legend_x = left + 12 + (index % 3) * 260
        legend_y = top + 22 + (index // 3) * 24
        elements.extend([
            (
                f'<line x1="{legend_x}" y1="{legend_y - 5}" '
                f'x2="{legend_x + 28}" y2="{legend_y - 5}" '
                f'stroke="{color}" stroke-width="3"/>'
            ),
            (
                f'<text class="legend" x="{legend_x + 36}" y="{legend_y}">'
                f"{escape(label)}</text>"
            ),
        ])

    for x_value, y_value in markers or []:
        elements.append(
            f'<circle cx="{sx(x_value):.1f}" cy="{sy(y_value):.1f}" r="5" '
            f'fill="{PLOT_COLORS[1]}" stroke="#ffffff" stroke-width="2"/>'
        )

    elements.extend([
        (
            f'<text class="label" x="{left + plot_width / 2}" '
            f'y="{SVG_HEIGHT - 25}" text-anchor="middle">'
            "Wavenumber (cm^-1)</text>"
        ),
        (
            f'<text class="label" x="25" y="{top + plot_height / 2}" '
            'text-anchor="middle" transform="rotate(-90 25 '
            f'{top + plot_height / 2})">Absorbance</text>'
        ),
        "</svg>",
    ])
    return "".join(elements)


def create_spectrum_plot(
    dataframe,
    title: str = "IR Spectrum",
    peaks=None,
    save_path: str | Path | None = None,
) -> str:
    """Create an SVG spectrum plot with optional highlighted peaks."""
    markers = []
    for peak in peaks or []:
        wavenumber = peak[0] if isinstance(peak, tuple) else peak
        index = (dataframe["wavenumber"] - wavenumber).abs().idxmin()
        markers.append((
            float(dataframe["wavenumber"].loc[index]),
            float(dataframe["absorbance"].loc[index]),
        ))

    svg = _render_svg(
        [(
            "IR Spectrum",
            dataframe["wavenumber"].to_numpy(),
            dataframe["absorbance"].to_numpy(),
        )],
        title,
        markers,
    )
    return _finish_plot(svg, save_path)


def create_comparison_plot(
    first_dataframe,
    second_dataframe,
    first_title: str = "Spectrum 1",
    second_title: str = "Spectrum 2",
    save_path: str | Path | None = None,
) -> str:
    """Create an overlaid SVG comparison of two spectra."""
    svg = _render_svg(
        [
            (
                first_title,
                first_dataframe["wavenumber"].to_numpy(),
                first_dataframe["absorbance"].to_numpy(),
            ),
            (
                second_title,
                second_dataframe["wavenumber"].to_numpy(),
                second_dataframe["absorbance"].to_numpy(),
            ),
        ],
        f"{first_title} vs {second_title}",
    )
    return _finish_plot(svg, save_path)


def create_overlaid_plot(
    spectra_data: dict,
    save_path: str | Path | None = None,
) -> str:
    """Create an SVG overlay for a mixture and compound references."""
    series = []
    for label, spectrum in spectra_data.items():
        if isinstance(spectrum, dict) and "wavenumber" in spectrum:
            series.append((
                label,
                np.asarray(spectrum["wavenumber"]),
                np.asarray(spectrum["absorbance"]),
            ))
        elif isinstance(spectrum, np.ndarray):
            series.append((label, COMMON_AXIS, spectrum))

    svg = _render_svg(series, "Multi-Compound IR Spectrum Analysis")
    return _finish_plot(svg, save_path)
