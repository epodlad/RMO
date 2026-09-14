# Scientific reproduction

The application retains the R139 scientific state. The web transport and packaging do not change the MHD equations, numerical tolerances or saved observational classifications. The interface preserves the distinction between model consistency, bounded search results and observational identification.

## Verified application cases

`verification/release_smoke.py` starts an isolated local service. It compares A63's returned assessment with the saved assessment, checks its PDF and request identity, and runs the B01 contact example with independent policy checks. `verification/public_service_smoke.py` checks session separation, public-origin behavior and shared calculation capacity at the HTTP boundary behind an HTTPS proxy. These are programmatic checks, not interactive browser acceptance.

## Scientific companion

Download `RMO_science_R139.zip` from **Scientific Archive R139**, DOI [10.5281/zenodo.22742107](https://doi.org/10.5281/zenodo.22742107), and extract it into a separate working directory. The top-level scientific folders, their `results/`, and `observational_pilot/` preserve the retained source inputs, saved numerical results and method code. File hashes are in `FILE_MANIFEST.json` and can be checked with `verify_manifest.py`. Historical per-study protocols describe the original executions; their old UI, package and full-snapshot paths are not instructions to rebuild this curated release.

For a bounded reproduction, copy the relevant study to a new output directory, inspect its per-study dependencies and input paths, and run its scientific calculation or figure script there. Original saved results should remain the comparison baseline. Some original protocols expect source data retrieved separately and the historical dependency versions in their runtime records. The entire R0–R139 campaign has not been rerun for this release.

The R133 temporal-bridge SVD cache was reconstructed from the retained `AIA_bridge_grids.npz`, using the original centering and empirical-noise algorithm. Both sets of singular values agree with the saved sensitivity record within `rtol=1e-12, atol=1e-9`; full-rank reconstruction error is below `1e-8` DN/s. Its `SVD_factors.verification.json` records actual errors and hashes. `code/recover_svd_cache.py` can repeat this cache-only operation into a new output file. Singular-vector signs and compressed bytes can depend on the numerical environment. The historical SVD interpretation warnings, including temporal information leakage, remain applicable.

The historical R107 PDF was truncated in both saved source copies. It is omitted; the usable original R107 figure, numerical records and scientific code remain. No invented PDF content replaces the damaged stream.

## R139 source profiles

The 12 profiles and all 1,620 retained rows in `completed_analysis/results/published_profiles.csv` were compared directly with the original workbook and agree exactly. This is a source-data consistency check, not a new Gaussian fit or new MHD classification.

To run `observational_pilot/e09_iris_R139/completed_analysis/reproduce_e09.py`, first obtain the original [Ye et al. Source Data workbook](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-75039-z/MediaObjects/41467_2026_75039_MOESM7_ESM.xlsx) through the [publisher's article page](https://doi.org/10.1038/s41467-026-75039-z). Place it beside that script with its original filename. Check its SHA-256 against `SOURCE_DATA.json` in that directory. The script reads source values and writes its own results; use a separate reproduction copy. The workbook's original source is linked instead of redistributed with modified metadata.

Original FITS byte streams are retained. Some archived AIA housekeeping header cards contain nonstandard `nan` values; these were not silently normalized. That limitation is separate from checks of the retained numerical results and the application's supported synthetic cases.
