# RMO software and scientific archives

## Current archived release

The **27 September 2026** software archive, **1.0.0+local-fan.20260927**, is published under DOI [10.5281/zenodo.22970620](https://zenodo.org/records/22970620). The application version remains **1.0.0**.

The archive includes the **Solar front · full MHD fan** and **Explore a front interaction** examples, their portable states and physical checks, and the updated Sun-and-folding-fan logo. The examples use explicitly chosen model states; their checks do not establish seven observed solar waves or a unique observational interpretation.

The complete `RMO-1.0.0-public-20260927.zip` contains 504 files from source commit `71d702dfc0c85cf63208feb17bb83950a22a85e5`. `SHA256SUMS.txt` gives the checksums of the ZIP and the separately supplied `RMO_logo.png`. No older archive or multipart assembly is required. After extraction, run `python verify_manifest.py` inside `RMO-1.0.0` to verify the distributed files.

The related preprint, *[Riemann Map Operator for Solar Front Diagnostics](https://arxiv.org/abs/2609.15210)*, is **submitted to Solar Physics**.

## Earlier software archives

The preceding [full-fan snapshot](https://doi.org/10.5281/zenodo.22966003) and [front-interaction snapshot](https://doi.org/10.5281/zenodo.22963649) remain available under their own DOIs.

RMO **1.0.0** is published on [GitHub](https://github.com/epodlad/RMO/releases/tag/v1.0.0) and archived as software under DOI [10.5281/zenodo.22905556](https://doi.org/10.5281/zenodo.22905556). The original 1.0.0 source snapshot is commit `67e48146088e9ddf8b27cd193881453baccd2240`.

The separate **Scientific Archive R139**, DOI [10.5281/zenodo.22742107](https://doi.org/10.5281/zenodo.22742107), preserves the scientific inputs, methods and retained results. Cite the software archive for the application and the scientific archive for those research materials; their scopes are distinct.

Earlier software versions remain available as [1.0.0-rc4](https://doi.org/10.5281/zenodo.22776018) and [1.0.0-rc3](https://doi.org/10.5281/zenodo.22741502). Citations to those versions continue to identify their respective records.

See [release verification](RELEASE_ACCEPTANCE.md) for the checks actually completed and their limitations, and [scientific reproduction](REPRODUCIBILITY.md) for provenance and reproduction guidance. The software release does not change the R139 scientific claims or imply complete MHD coverage or observational identification.
