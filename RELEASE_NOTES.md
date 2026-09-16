# RMO 1.0.0-rc4 — interface correction, 2026-09-16

The input workflow now follows the reading order: choose an example, inspect or enter parameters, check the input, calculate, and save the result. The synthetic Calculate button sits below the check report. An extra Check button is available at the end of the parameter form.

New local diagnoses open at the result. Both saved and new results offer a direct return to their parameters. An empty-input route supports entering normalized model parameters by hand; field errors name the quantity and appear beside Calculate. Input changes invalidate prior results, and cancelled or late responses remain separate history.

Solar literature cards open at the selected event, offer direct edit/review controls and place the review after the working values. Labels distinguish published values, editable constraints, saved assessments and newly calculated results. On narrow screens, the local and solar input tables become vertical groups with visible field labels. Frame arrows have text labels, and controls have larger touch targets and visible keyboard focus.

Automated checks passed; real-browser visual acceptance of this correction remains pending. See `docs/RELEASE_ACCEPTANCE.md`. Numerical Python code, saved scientific data, R139 results and assets are unchanged. This package keeps rc4 and requests no new DOI. Publication instructions are in `docs/RELEASE_ZENODO.md`.

## Previously published rc4 changes, 2026-09-15

### SUVI preview restoration

The 10 September 2017 SUVI example once again plays inside RMO. This update restores the 51-frame original/base-difference/running-difference viewer, the saved original/base-difference/base-ratio video, and the event-card still. The viewer starts at frame 23, retains frame stepping and playback controls, and loads only when opened.

All 51 cropped JPEGs match the first 101 frames of NOAA's GOES-16/SUVI 195 Å animation at every second video frame. NOAA SWPC credit, the official animation and Seaton and Darnel (2018) are linked beside the media. Original JPEG bytes, saved difference images and the comparison MP4 are preserved. No Helioviewer download origin or calibrated observing cadence is inferred.

R139 numerical results, model assumptions and the calculation implementation are unchanged. The original scientific companion remains DOI [10.5281/zenodo.22742107](https://doi.org/10.5281/zenodo.22742107). The rc4 software was archived as DOI 10.5281/zenodo.22776018; it does not change the archived rc3 tag. Attribution and reuse guidance are in `THIRD_PARTY_NOTICES.md`, and the source comparison is in `docs/SUVI_MEDIA_PROVENANCE.json`.

The QuickLook opening now places the SUVI viewer above its explanation and gives an expanded example the full row. A short visual guide introduces connected plasma evolution using the manuscript's simple-wave panel and lower Riemann fan. The header links to the preprint [arXiv:2609.15210](https://arxiv.org/abs/2609.15210). The guide distinguishes the wider Riemann picture from the current local diagnostic tests.

## Previous release: RMO 1.0.0-rc3 — R139

RMO provides a QuickLook interface for examining local ideal-MHD interpretations under declared inputs and assumptions.

Use the hosted application at **https://rmo-solar.org/**.

This release candidate contains the application source, reviewed presentation assets, citation metadata, Apache-2.0 license and third-party notices. It preserves the R139 scientific state and the established interface.

The hosted navigation fix enables external links to open the landing page while retaining the existing Host, API-origin, token and session checks. Targeted hosted checks cover A63 diagnosis and exports, B01 contact calculations and a normal/incognito comparison. The custom-domain calculation was checked using the maintainer's report and result excerpts. Details and evidence limits are in [docs/RELEASE_ACCEPTANCE.md](docs/RELEASE_ACCEPTANCE.md).

Complete interactive coverage and production load testing remain open. Supported local classes and saved Brio–Wu solutions do not establish full MHD branch coverage, uniqueness or observational identification.

The software release is archived at DOI [10.5281/zenodo.22741502](https://doi.org/10.5281/zenodo.22741502), corresponding to tag `v1.0.0-rc3` and commit `ff6fdf7b289d32b20d4185d57c4e96bbe7a1f40f`. The scientific companion `RMO_science_R139.zip` is published separately as **Scientific Archive R139**, DOI [10.5281/zenodo.22742107](https://doi.org/10.5281/zenodo.22742107). It is not needed to run the application.

Original RMO code: **Apache-2.0**. Third-party software, fonts, data and source acknowledgements retain their respective terms in `THIRD_PARTY_NOTICES.md`.
