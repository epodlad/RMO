# RMO — Riemann Map Operator

**A bright front moves across the Sun. What is the plasma doing?**

A solar flare or a sudden expansion of a coronal mass ejection can set the surrounding plasma into motion. Shocks, expanding regions and moving boundaries may develop together as parts of one connected wave pattern.

**RMO asks which connections between neighbouring plasma states are compatible with the observations.** Density, pressure, plasma flow and magnetic field must change together according to the physical equations. The connections that remain possible form a Riemann map.

QuickLook helps you compare possible explanations, inspect the supporting checks and identify which additional measurement could distinguish them. Start with a supplied model or a published solar event; you do not need to enter numbers to explore the examples.

**[Open RMO QuickLook](https://rmo-solar.org/) · [Download the published rc4 archive](https://doi.org/10.5281/zenodo.22776018) · [Read the paper](https://arxiv.org/abs/2609.15210)**

Prepared version: **1.0.0** (unpublished release draft) · Scientific reference: **R139** · Author: **Olena Podladchikova**.

This branch prepares the stable release. Publication is pending the phone-layout check and an explicit archiving decision that respects the existing DOI. The live site and the DOI-linked archive remain rc4 until publication. See [release preparation](docs/RELEASE_PREPARATION_20260922.md).

## Two ways to use RMO

### 1. Online — use the website

Open **[rmo-solar.org](https://rmo-solar.org/)** in your browser. The website provides the QuickLook interface and a hosted Python calculation service. Supported new calculations run on that server; you do not need to install Python or download the code.

- **Solar events:** inspect published measurements, edit a working copy, review its constraints and save a literature draft as JSON.
- **Model examples:** explore supplied models, their results, plots and physical checks.
- **Contact / enter values:** load a synthetic contact example or enter values, check the input and calculate a supported case.

Download your input, result JSON and any available PDF from the interface to keep your work. Available calculations depend on the selected model and its supported input domain. Literature-event reviews and saved examples are labelled separately from newly calculated results.

### 2. On your computer — download and run the code

Download the complete application ZIP from [Zenodo](https://doi.org/10.5281/zenodo.22776018), or use **Code → Download ZIP** on [GitHub](https://github.com/epodlad/RMO). Extract the archive and open a terminal in the folder containing `requirements.txt`.

The verified runtime is **Python 3.12.14**, with dependencies pinned in `requirements.txt`. Install them in a virtual environment, then start the local Python server.

**Linux / macOS:**

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -B -m local_app.server --port 8765
```

**Windows — Command Prompt:**

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -B -m local_app.server --port 8765
```

Open **[http://127.0.0.1:8765](http://127.0.0.1:8765)** in a browser. The interface and calculations now run on your computer. Keep the terminal and Python process open while using the application. Opening `public/index.html` directly does not start the calculation service or resolve all assets.

Local completed requests and results are written under `results/local_runs/`, in a new directory for each server session. Set `RMO_RESULTS_DIR` to choose a different output parent. Existing session directories are not overwritten. The interface also offers portable JSON and, where available, PDF downloads.

## What the results mean

The current application tests local connections around a selected front within ideal magnetohydrodynamics (MHD). Results depend on the available measurements, stated assumptions, implemented models and search limits. Missing measurements remain unknown, and a front's image-pattern speed is kept distinct from the plasma velocity.

A literature-input review does not by itself determine the observed wave type. A supported local model does not establish a unique global Riemann solution, stability or exhaustive coverage of every MHD wave family. Reconstructing an eruption's complete wave pattern remains a wider goal.

## Software and scientific reproduction

This repository contains the application source, required fixtures, reviewed presentation assets, documentation, licences and validation records. The separate [Scientific Archive R139](https://doi.org/10.5281/zenodo.22742107) contains retained scientific code, data, assessments and figures; see [scientific reproduction](docs/REPRODUCIBILITY.md). That companion is not required to start this application.

The **16 September 2026 interface correction**, through commit `89c15b7`, improves input and calculation guidance, adds direct navigation to solar events and models, and places review and save actions beside their results. It keeps the rc4 version label, numerical solvers and R139 scientific results. The SUVI preview, comparison video and event-card still retain their source attribution.

Automated checks and the scope of completed and remaining browser checks are documented in [release acceptance](docs/RELEASE_ACCEPTANCE.md). After installing dependencies, run the application smoke checks with:

```sh
python -B verification/release_smoke.py
```

These targeted checks are not a claim of complete interactive acceptance, exhaustive MHD coverage or load testing.

## Hosting your own web service

[Render setup](docs/DEPLOY_RENDER.md) documents the included `render.yaml`, runtime dependencies and public-server entry point `python -B -m web_app.server`. The hosted configuration uses one Python process, separate session tokens and bounded calculation workers. Only reviewed static assets are served; public results are retained through browser downloads rather than exposed in a shared results directory.

## Citation and rights

For the corrected rc4 application, cite DOI **[10.5281/zenodo.22776018](https://doi.org/10.5281/zenodo.22776018)** and identify the dated interface correction where relevant. The earlier rc3 DOI **[10.5281/zenodo.22741502](https://doi.org/10.5281/zenodo.22741502)** remains valid for that version; it identifies tag [`v1.0.0-rc3`](https://github.com/epodlad/RMO/releases/tag/v1.0.0-rc3), commit `ff6fdf7b289d32b20d4185d57c4e96bbe7a1f40f`. Use the DOI for the version actually used. See [Zenodo publication details](docs/RELEASE_ZENODO.md).

When using the scientific companion's data, figures or analyses, also cite **Scientific Archive R139**, DOI [10.5281/zenodo.22742107](https://doi.org/10.5281/zenodo.22742107), and the original sources relevant to the study.

Original RMO code is licensed under **Apache-2.0**. Third-party code, fonts and observational data retain their own terms and acknowledgements; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). SUVI imagery and video retain NOAA SWPC attribution, with Seaton and Darnel (2018) as the scientific reference.
