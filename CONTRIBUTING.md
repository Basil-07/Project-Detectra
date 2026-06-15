# Contributing

## Development Workflow

1. Create and activate a Python 3.11 virtual environment.
2. Install `requirements-dev.txt`.
3. Create a focused branch for the change.
4. Keep analysis logic out of Flask route handlers when adding new behavior.
5. Run `pytest` and `ruff check .` before opening a pull request.

## Code Conventions

- Follow PEP 8 and keep lines readable at approximately 100 characters.
- Use descriptive module, function, and variable names.
- Add docstrings to public modules and non-obvious functions.
- Add comments for intent or scientific assumptions, not line-by-line narration.
- Use `pathlib.Path` and the constants in `detectra.paths` for filesystem access.
- Never replace failed analysis with fabricated predictions.

## Data and Models

- Do not commit generated plots, uploaded samples, reports, caches, or local
  evaluation output.
- Reference spectra belong in `data/reference_spectra/`.
- Serialized models are generated locally under `models/` and are ignored by
  Git. Commit training code and documented metrics, not `.pkl` outputs.
- Document the training data, dependency versions, and evaluation metrics when
  changing model-training behavior.
- Treat pickle/joblib files as trusted artifacts only; never load models from
  untrusted users.

## Pull Requests

Describe the behavior changed, tests run, and any model or dataset impact.
Screenshots are useful for frontend changes. Model changes should include
before-and-after metrics and a reproducible training command.
