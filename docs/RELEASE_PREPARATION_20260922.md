# RMO 1.0.0 release preparation — 22 September 2026

Status: **deployed; GitHub stable release not published**. Preparation baseline: `aff327887a44ddf2471e840b3a34d0d21f5a809c`; scientific state: R139.

This branch assembles the rc4 interface corrections into the proposed stable version. It updates version metadata and release documentation. Numerical solvers, scientific records and reviewed assets are unchanged.

## Completed

- Merged PR #5; Render deployed commit `3b2be8769d6030e23e02aea0ff4f86f648234bbe`. The post-deploy root and health checks confirmed 1.0.0.
- On a real Android phone, calculated default contact speed 0.2 and edited speed 0.45. The screenshots show the matching text and plots. Both exported results were parsed; request snapshots/checksums agree and both policy validations pass. Six uploaded files contain three byte-identical copies of each result.
- On the live desktop site, calculated the edited contact at 0.45 and verified its downloaded result and both policy checks.
- Calculated A63 with preset factor 0.05 and front-speed half-width 0.04, inspected input/result JSON and the PDF, restored the saved input after changing the field, and recalculated.
- Edited E05 from published 590 to working 600 km/s, reviewed, saved, switched to E04, imported E05 and reviewed again. Published and working values stay separate; this remains an input review.
- Exercised SUVI loading, frame stepping and playback, checked keyboard focus, and verified the www-to-apex redirect.
- With the pinned Python 3.12.14 / aiohttp 3.14.3 runtime, passed 21 local HTTP checks, 14 public HTTP checks, 44 navigation checks and two asset-cache tests. The earlier 546 DOM/API assertions are retained as dated evidence, not claimed as a fresh run.

The machine-readable report records scope, file hashes and limitations: [FINAL_RELEASE_ACCEPTANCE_20260922.json](FINAL_RELEASE_ACCEPTANCE_20260922.json).

## Prepared interface follow-up (not deployed)

The maintainer requested equal visibility for Fast shock, Slow shock, Contact and Rotation. Four matching buttons now appear at the top and inside Model examples, each labelled **Open saved example**. They load exact saved A63/A17/A42/A88 results through the existing workflow. They do not start a new calculation. The input-check button now says **Check input values**, with step 3 retained only in its heading.

Workflow notices and local-model outcomes use the page theme colours; the affected header links receive readable dark-theme colours. All **557 DOM/API workflow checks** pass, including each shortcut and rejection of a late response after selecting another example. All 37 inline scripts parse and all 14 embedded JSON blocks are unchanged. See [follow-up evidence](MODEL_SHORTCUTS_ACCEPTANCE_20260922.json). Deployment and visual confirmation of this follow-up remain pending.

## Before publication

1. Complete the remaining phone checks: A63 bound edit and saved-input import, JSON/PDF download, solar-card working-value review and draft save/import, viewer controls and www redirect. The contact edit/calculate/JSON workflow has passed. Review the low-contrast links and completion notice visible in dark phone screenshots. The repeated step 3 label was noted by the maintainer, who confirmed the action was understandable.
2. Resolve the final archiving policy. The published rc4 DOI is **10.5281/zenodo.22776018** and the maintainer asked to keep it. A new GitHub release with the Zenodo integration enabled may create a new archive. Do not publish until this is settled. Do not retag or overwrite the scientific R139 deposit.
3. Update the draft release to the merged and deployed source, include the final scoped acceptance record, then publish under the agreed archiving policy after the remaining checks.

The deployed site is live; the GitHub stable release remains a reviewable draft and no new DOI is claimed. Production load testing and complete MHD coverage are outside this acceptance claim.
