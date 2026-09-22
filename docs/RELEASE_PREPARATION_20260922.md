# RMO 1.0.0 release preparation — 22 September 2026

Status: **prepared, not published**. Baseline: `aff327887a44ddf2471e840b3a34d0d21f5a809c`; scientific state: R139.

This branch assembles the rc4 interface corrections into the proposed stable version. It updates version metadata and release documentation. Numerical solvers, scientific records and reviewed assets are unchanged.

## Completed

- On the live desktop site, calculated the edited contact at 0.45 and verified its downloaded result and both policy checks.
- Calculated A63 with preset factor 0.05 and front-speed half-width 0.04, inspected input/result JSON and the PDF, restored the saved input after changing the field, and recalculated.
- Edited E05 from published 590 to working 600 km/s, reviewed, saved, switched to E04, imported E05 and reviewed again. Published and working values stay separate; this remains an input review.
- Exercised SUVI loading, frame stepping and playback, checked keyboard focus, and verified the www-to-apex redirect.
- With the pinned Python 3.12.14 / aiohttp 3.14.3 runtime, passed 21 local HTTP checks, 14 public HTTP checks, 44 navigation checks and two asset-cache tests. The earlier 546 DOM/API assertions are retained as dated evidence, not claimed as a fresh run.

The machine-readable report records scope, file hashes and limitations: [FINAL_RELEASE_ACCEPTANCE_20260922.json](FINAL_RELEASE_ACCEPTANCE_20260922.json).

## Before publication

1. Check the live interface on a phone: open Contact / enter values and Model examples, inspect the vertical parameter fields and Calculate controls, and confirm that the solar comparison and Save controls are readable. Browser resizing/device emulation was unavailable in this session; no phone pass is claimed.
2. Resolve the final archiving policy. The published rc4 DOI is **10.5281/zenodo.22776018** and the maintainer asked to keep it. A new GitHub release with the Zenodo integration enabled may create a new archive. Do not publish until this is settled. Do not retag or overwrite the scientific R139 deposit.
3. Merge the reviewed candidate, deploy that commit, verify the 1.0.0 identity and contact workflow, then publish the release under the agreed archiving policy.

The draft is reviewable without changing the live site or publishing a new DOI. Production load testing and complete MHD coverage are outside this acceptance claim.
