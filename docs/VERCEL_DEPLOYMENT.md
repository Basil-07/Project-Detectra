# Deploying Detectra to Vercel

Detectra is configured for Vercel's Python 3.12 runtime. The web application is
serverless, generated files use `/tmp`, static assets are served from `public/`,
and model files are downloaded from a GitHub Release when first needed.

## Important Limitations

- Do not train models on Vercel.
- The first pure or multi-compound request after a cold start is slower because
  the model archive must be downloaded and loaded.
- `/tmp` is ephemeral and may be cleared between invocations.
- Serverless PDF reports contain the analysis summary but may omit plots,
  because temporary plots are not guaranteed to exist in a later invocation.
- Vercel request/response and function bundle limits still apply. If the
  scientific dependency bundle exceeds your plan's limit, deploy the backend
  to a conventional Python host instead.

## 1. Use Python 3.12 Locally

Create a clean Python 3.12 environment. Models should be retrained with the
same dependency versions used by Vercel.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### macOS or Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 2. Retrain the Models

Do not reuse pickles created with older Python, scikit-learn, or XGBoost
versions. The Vercel-compatible ensemble intentionally excludes CatBoost
because its wheel pushes the function bundle beyond Vercel's size limit.

```text
python -m detectra.training.train_models
```

Confirm all five artifacts:

```text
python -m detectra.training.train_models --check
```

## 3. Create the Release Archive

```text
python -m detectra.training.package_models
```

This creates:

```text
dist/detectra-models.zip
```

The command also prints a SHA256 checksum. Keep that value. It will refuse to
package a legacy ensemble that still contains CatBoost.

## 4. Publish the Model Archive

1. Push the source repository to GitHub.
2. Open the repository's **Releases** page.
3. Select **Draft a new release**.
4. Use a tag such as `models-v1`.
5. Upload `dist/detectra-models.zip` as a release asset.
6. Publish the release.
7. Copy the direct asset URL. It should resemble:

```text
https://github.com/OWNER/REPOSITORY/releases/download/models-v1/detectra-models.zip
```

Do not add the archive or `.pkl` files to the Git repository.

## 5. Import the Repository into Vercel

1. Sign in to Vercel and select **Add New Project**.
2. Import the Detectra GitHub repository.
3. Use **Other** as the framework preset if Vercel does not detect Python.
4. Keep the repository root as the root directory.
5. Do not set an output directory.
6. Vercel will install `requirements.txt` automatically.

The repository already contains:

- `app.py` as the native Flask entry point detected by Vercel
- `vercel.json` for Vercel configuration validation
- `.vercelignore` to reduce the deployment bundle
- `public/static/` for CSS and the logo

## 6. Add Environment Variables

In **Project Settings > Environment Variables**, add:

### `DETECTRA_SECRET_KEY`

A long random value. Generate one locally:

```text
python -c "import secrets; print(secrets.token_hex(32))"
```

### `DETECTRA_MODELS_URL`

The direct GitHub Release asset URL from step 4.

### `DETECTRA_MODELS_SHA256`

The checksum printed by `package_models`. This is optional but strongly
recommended.

Add the variables to Production and Preview environments as needed.

## 7. Deploy

Select **Deploy** and monitor the build logs. After deployment, open:

```text
https://YOUR-PROJECT.vercel.app/health
```

Expected response:

```json
{
  "status": "ok",
  "serverless": true,
  "pure_models_available": true,
  "multi_models_available": true
}
```

The availability fields indicate that local models exist or the release URL is
configured. They do not download the archive.

## 8. Test the Production Application

1. Open the home page.
2. Run mixture simulation first; it does not require model downloads.
3. Upload `data/reference_spectra/cocaine.csv` under Pure Analysis.
4. Expect the first request to take longer while models are downloaded.
5. Run a small multi-compound analysis.
6. Test PDF downloads.
7. Review Vercel function logs for memory, timeout, or bundle-size errors.

## Updating Models

When training changes:

1. Retrain under Python 3.12.
2. Create a new archive.
3. Publish a new GitHub Release tag such as `models-v2`.
4. Update `DETECTRA_MODELS_URL` and `DETECTRA_MODELS_SHA256` in Vercel.
5. Redeploy.

## Troubleshooting

### Function bundle is too large

The Vercel-compatible stack excludes CatBoost. Its pinned Linux wheels measure
about 336.1 MiB uncompressed before source files, below Vercel's 500 MB
function limit.
Confirm that `.vercelignore` is present. If the final deployment still exceeds
your plan's limit, use a separate ML backend on Render, Railway, Fly.io, or a
VM.

### Model download times out

Confirm the release asset is public and the URL points directly to the ZIP.
Check the function logs and checksum value.

### Model deserialization fails

Retrain the models in a clean Python 3.12 environment using the exact versions
in `requirements.txt`, recreate the archive, and update the release.

### Plot URL returns 404

Serverless result plots should be embedded as data URLs. Confirm the deployment
has `VERCEL=1`, which Vercel supplies automatically.
