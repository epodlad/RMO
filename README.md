# RMO — Riemann Map Operator

RMO connects declared solar-observation constraints with admissible local ideal-MHD interpretations. This release candidate preserves the R139 scientific results and the established QuickLook interface, including 38 analysis links, input forms, scientific image viewers, saved assessments and version history.

The calculations are conditional on the stated model, inputs and search limits. A supported local class does not establish a unique global Riemann solution or identify an observed solar front by itself. The interface keeps these distinctions beside the results.

## Run locally

Use Python 3.12.14. From this repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -B -m local_app.server --port 8765
```

Open http://127.0.0.1:8765 in a browser. On Windows, activate `.venv\Scripts\activate` instead. Keep the Python process running while using the calculation forms. The application is served from this process; opening `public/index.html` directly does not enable calculations or resolve all assets.

Local completed requests/results are written to a new directory under `results/local_runs/` for each server session. Set `RMO_RESULTS_DIR` to choose a different output parent. Existing output directories are not overwritten. Download the input JSON, result JSON and available PDF from the interface to retain a portable record.

## Web service

[Render setup](docs/DEPLOY_RENDER.md) uses the included `render.yaml`, one Python process and the supplied runtime dependencies. Public sessions receive separate request tokens. Only reviewed static assets are served; request bodies, calculation results and execution-machine details are not exposed as shared files. Public results are retained through the browser's downloads. One calculation runs at a time, with the existing bounded worker limits.

## Scientific reproduction

The application repository contains the runtime source, required fixtures and the reviewed presentation assets. The separate `RMO_science_R139.zip` companion contains retained scientific code, data, assessments and figures. See [scientific reproduction](docs/REPRODUCIBILITY.md). It is a companion archive for Zenodo, not a build dependency for Render.

Run the application smoke checks after installing dependencies:

```sh
python3 -B verification/release_smoke.py
```

The release validation report distinguishes HTTP/scientific checks from browser acceptance. Full interactive browser acceptance and the first hosted deployment remain release-candidate gates.

## Citation and rights

Use `CITATION.cff` for the software citation. No DOI is assigned in this package. See [Zenodo preparation](docs/RELEASE_ZENODO.md).

Original RMO code is distributed under Apache-2.0. Third-party code, fonts and observational data retain their own terms and acknowledgements: see `THIRD_PARTY_NOTICES.md`. Source links replace published figures and the 2017 preview sequence whose exact redistribution basis was not established. This does not change the retained scientific numerical results.
