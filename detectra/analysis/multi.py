import numpy as np
import pandas as pd
from detectra.paths import DATA_DIR

# === Define ===
COMMON_AXIS = np.linspace(4000, 400, 900)
# Ensure paths are correct relative to where app.py runs
compound_files = {
    name: DATA_DIR / f"{name}.csv"
    for name in (
        "cocaine",
        "morphine",
        "heroin",
        "methadone",
        "meth",
        "sucrose",
        "lactic",
        "glucose",
        "ethanol",
        "citric",
    )
}
valid_compounds = list(compound_files.keys())
drug_compounds = ["cocaine", "morphine", "heroin", "methadone", "meth"]

# === Load & Interpolate ===
def load_and_interpolate_spectrum(path):
    df = pd.read_csv(path, usecols=["wavenumber", "absorbance"])
    x = df["wavenumber"].values
    y = df["absorbance"].values
    if x[0] > x[-1]:
        x = x[::-1]
        y = y[::-1]
    return np.interp(COMMON_AXIS, x, y)

# No if __name__ == "__main__": block here.
# This script is now purely a module for app.py to import and use its functions.
