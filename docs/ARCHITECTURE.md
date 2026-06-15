# Architecture

## Web Layer

`detectra.web` assembles the Flask application. `detectra.routes` owns HTTP
request orchestration and session state. Reusable web concerns are separated
under `detectra.services`:

- `validation`: uploaded CSV validation
- `model_artifacts`: model inventory and first-run status
- `plotting`: lightweight SVG spectrum rendering
- `reporting`: dependency-free PDF composition
- `runtime_files`: generated-file cleanup

Runtime files are written under `instance/` and are excluded from Git.

## Pure Spectrum Analysis

`detectra.analysis.pure` converts a spectrum into summary statistics, detected
peak features, drug-specific peak matches, and derivative features. A binary
XGBoost pipeline first estimates drug presence. Samples above the configured
threshold are passed to a multiclass XGBoost pipeline for compound identity.

```text
CSV -> validation -> feature extraction -> binary model
                                      -> multiclass model -> result
```

## Mixture Simulation

`detectra.analysis.mixture` generates Gaussian bands from known characteristic
peaks, combines compounds by percentage, adds noise, and smooths the result.
Peak matching compares detected local maxima with expected drug peaks.

This mode is a simulation. It does not classify an independently measured
mixture.

## Multi-Compound Analysis

`detectra.analysis.multi` interpolates each reference spectrum onto a common
900-point axis. Selected spectra are averaged and passed through five classifier
chains. Majority voting produces the final multi-label drug prediction.

## Training

`detectra.training.train_multi` creates synthetic combinations from the
reference spectra and trains the classifier-chain ensemble. Because training
and evaluation derive from the same small reference library, these metrics
must not be presented as independent real-world validation.

## Artifact Boundaries

- `data/reference_spectra/`: version-controlled scientific inputs
- `models/`: ignored, locally trained model artifacts
- `public/static/`: version-controlled frontend assets served by Flask locally
  and Vercel's CDN in production
- `instance/`: ignored runtime and evaluation output
