"""Matplotlib rendering helpers for spectrum visualizations."""

import base64
import io
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns

from detectra.analysis.multi import COMMON_AXIS


plt.style.use("seaborn-v0_8")
sns.set_palette("husl")

PLOT_COLORS = ("#2569ad", "#d14f5b", "#258f72", "#d9822b", "#7656b4", "#8a6642")


def _finish_plot(save_path: str | Path | None) -> str:
    """Save the current figure or return it as a base64 data URL."""
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()
        return str(save_path)

    image_buffer = io.BytesIO()
    plt.savefig(image_buffer, format="png", dpi=300, bbox_inches="tight")
    image_buffer.seek(0)
    encoded = base64.b64encode(image_buffer.getvalue()).decode()
    plt.close()
    return f"data:image/png;base64,{encoded}"


def create_spectrum_plot(
    dataframe,
    title: str = "IR Spectrum",
    peaks=None,
    save_path: str | Path | None = None,
) -> str:
    """Create an IR spectrum plot with optional highlighted peaks."""
    plt.figure(figsize=(12, 8))
    plt.plot(
        dataframe["wavenumber"],
        dataframe["absorbance"],
        color=PLOT_COLORS[0],
        linewidth=2,
        label="IR Spectrum",
    )

    if peaks:
        peak_wavenumbers = [
            peak[0] if isinstance(peak, tuple) else peak for peak in peaks
        ]
        peak_indices = [
            (dataframe["wavenumber"] - wavenumber).abs().idxmin()
            for wavenumber in peak_wavenumbers
        ]
        if peak_indices:
            plt.scatter(
                dataframe["wavenumber"].loc[peak_indices],
                dataframe["absorbance"].loc[peak_indices],
                color=PLOT_COLORS[1],
                s=80,
                zorder=5,
                label="Detected Peaks",
            )

    plt.xlabel("Wavenumber (cm^-1)", fontsize=14)
    plt.ylabel("Absorbance", fontsize=14)
    plt.title(title, fontsize=16, fontweight="bold")
    plt.grid(True, alpha=0.2)
    plt.legend()
    plt.gca().invert_xaxis()
    return _finish_plot(save_path)


def create_comparison_plot(
    first_dataframe,
    second_dataframe,
    first_title: str = "Spectrum 1",
    second_title: str = "Spectrum 2",
    save_path: str | Path | None = None,
) -> str:
    """Create a side-by-side comparison of two spectra."""
    figure, (first_axis, second_axis) = plt.subplots(1, 2, figsize=(16, 6))
    for axis, dataframe, title, color in (
        (first_axis, first_dataframe, first_title, PLOT_COLORS[0]),
        (second_axis, second_dataframe, second_title, PLOT_COLORS[1]),
    ):
        axis.plot(
            dataframe["wavenumber"],
            dataframe["absorbance"],
            color=color,
            linewidth=2,
        )
        axis.set_xlabel("Wavenumber (cm^-1)")
        axis.set_ylabel("Absorbance")
        axis.set_title(title, fontweight="bold")
        axis.grid(True, alpha=0.2)
        axis.invert_xaxis()

    figure.tight_layout()
    return _finish_plot(save_path)


def create_overlaid_plot(
    spectra_data: dict,
    save_path: str | Path | None = None,
) -> str:
    """Create an overlaid plot for a mixture and compound references."""
    plt.figure(figsize=(14, 8))
    for index, (label, spectrum) in enumerate(spectra_data.items()):
        color = PLOT_COLORS[index % len(PLOT_COLORS)]
        if isinstance(spectrum, dict) and "wavenumber" in spectrum:
            plt.plot(
                spectrum["wavenumber"],
                spectrum["absorbance"],
                color=color,
                linewidth=2,
                label=label,
            )
        elif isinstance(spectrum, np.ndarray):
            plt.plot(
                COMMON_AXIS,
                spectrum,
                color=color,
                linewidth=2,
                label=label,
            )

    plt.xlabel("Wavenumber (cm^-1)", fontsize=14)
    plt.ylabel("Absorbance", fontsize=14)
    plt.title("Multi-Compound IR Spectrum Analysis", fontsize=16, fontweight="bold")
    plt.grid(True, alpha=0.2)
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.gca().invert_xaxis()
    return _finish_plot(save_path)
