# RMO — Riemann Map Operator

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22741502.svg)](https://doi.org/10.5281/zenodo.22741502)

**Use the hosted application: [rmo-solar.org](https://rmo-solar.org/).**

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

The hosted application has completed the targeted browser smoke checks documented in [release acceptance](docs/RELEASE_ACCEPTANCE.md): A63 local diagnosis and exports, B01 contact calculations, and a normal/incognito comparison. The same report records the custom-domain check and the remaining interactive coverage. This is version 1.0.0-rc3; complete interactive acceptance, full MHD branch coverage and load testing are not claimed.

## Citation and rights

Cite the archived software release **1.0.0-rc3** using DOI [10.5281/zenodo.22741502](https://doi.org/10.5281/zenodo.22741502). Machine-readable citation metadata is in `CITATION.cff`. This DOI identifies the source at tag [`v1.0.0-rc3`](https://github.com/epodlad/RMO/releases/tag/v1.0.0-rc3), commit `ff6fdf7b289d32b20d4185d57c4e96bbe7a1f40f`. Later documentation updates on `main` are outside that archived snapshot. See [Zenodo publication details](docs/RELEASE_ZENODO.md).

Original RMO code is distributed under Apache-2.0. Third-party code, fonts and observational data retain their own terms and acknowledgements: see `THIRD_PARTY_NOTICES.md`. Source links replace published figures and the 2017 preview sequence whose exact redistribution basis was not established. This does not change the retained scientific numerical results.
