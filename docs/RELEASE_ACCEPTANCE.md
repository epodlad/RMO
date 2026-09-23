# RMO 1.0.0 verification

RMO 1.0.0 is published on [GitHub](https://github.com/epodlad/RMO/releases/tag/v1.0.0) and [Zenodo](https://doi.org/10.5281/zenodo.22905556). The original 1.0.0 source snapshot is commit `67e48146088e9ddf8b27cd193881453baccd2240`; deployment of that commit on Render was confirmed live on 22 September 2026. This archive includes subsequent documentation-only corrections; its numerical source and scientific data remain those of the original snapshot. The scientific reference remains R139.

The recorded checks have the following scope:

- The pinned runtime passed 21 local HTTP, 14 public HTTP and 44 navigation checks, plus two asset-cache tests. The interface follow-up passed 557 DOM/API assertions; 37 executable inline scripts parsed and 14 embedded JSON data blocks were unchanged. DOM checks use an isolated Python API and do not render pixels.
- Desktop checks covered an edited contact at 0.45, A63 bound editing and JSON/PDF export and input import, E05 working-value review and draft save/import, SUVI frame stepping and playback, keyboard focus and the www redirect. Subsequent live desktop checks confirmed that the Fast shock and Rotational discontinuity shortcuts open their saved models.
- On a real Android phone, contacts at 0.2 and 0.45 produced matching text and plots. Both downloaded result JSON files were inspected: request snapshots and checksums match, with 37/37 independent checks passing for each of two policies. These phone checks apply to the initial 1.0.0 deployment, before the shortcut and theme follow-up.

Other phone workflows and the follow-up's phone layout remain unverified. These are scoped checks, not complete browser coverage, production load testing, or a new scientific validation campaign. They do not establish full MHD branch coverage, global uniqueness, stability or observational identification.

## Historical verification records

The dated sections and JSON reports below preserve the conditions and outcomes of earlier checks. Their release-candidate versions, deployment states and pending items describe those dates, not the current publication status. The latest automated interface evidence is in [MODEL_SHORTCUTS_ACCEPTANCE_20260922.json](MODEL_SHORTCUTS_ACCEPTANCE_20260922.json); desktop and Android evidence is in [FINAL_RELEASE_ACCEPTANCE_20260922.json](FINAL_RELEASE_ACCEPTANCE_20260922.json).

## 2026-09-22: temporary calculation capacity feedback

Both the contact and local-diagnosis interfaces now distinguish an occupied calculation slot from a connection failure. The user is asked to wait briefly and click Calculate again; entered values remain in the form. No calculation is queued or started automatically. The server returns a structured `CALCULATION_BUSY` response and does not consume the rejected attempt identifier.

Fourteen public HTTP checks and 546 DOM/API assertions pass. A real two-session check confirms that a second request can retry unchanged after the first finishes. UI checks confirm preserved inputs, no stale result, visible wait guidance, and enabled retry for both routes. Python 3.12.14, aiohttp 3.13.5 and jsdom 26.1.0 were used; this is not a production load test. See `BUSY_RESPONSE_ACCEPTANCE_20260922.json`.

The baseline commit `3eae090` is confirmed live on Render. Its contact workflow was exercised in a browser with both normal velocities set to 0.45, returning contact speed 0.45. Browser verification of the new busy message and final-release gates remains pending.

## 2026-09-17: bandwidth optimization (pending deployment)

The header image remains eager; the other 117 image elements use native browser lazy loading. All image sources, scientific text, embedded scripts, data and video controls are preserved. Browser scheduling determines when an offscreen image is fetched.

Only allowlisted, SHA-256-named public assets receive `public, max-age=31536000, immutable`. Session HTML, API responses and errors retain `no-store`. Two HTTP regression tests in `verification/test_asset_cache.py` pass, covering asset responses, ETag/304 revalidation, private routes and cross-site rejection. All executable inline scripts pass Node syntax checks, and the file manifest verifies.

These checks used the available local aiohttp 3.13.5 runtime, not the pinned production version. Browser transfer measurements and production verification remain pending; no measured bandwidth reduction is claimed yet. Version remains 1.0.0-rc4 and scientific state R139.

## 2026-09-16: follow-up navigation and saving correction

Update baseline: `ef4f83adb122c643dbe0065505fbae3c26f452d6` (`Update Zenodo metadata`), including the preceding UI commit `fd12152d64b490b049da73c39beb9cc2014798a7`. Version remains **1.0.0-rc4**, scientific state R139.

On that baseline, maintainer screenshots show a completed contact calculation after both normal velocities changed to 0.45. The E05 workflow changed image speed 590 → 600, saved a draft, restored 600 and completed another review. The exported draft was independently parsed: published 590, working/reviewed 600, calculation NOT_RUN and publication NOT_PUBLISHED. These checks exposed navigation problems addressed by this follow-up.

For the revised code, **544 DOM/API assertions passed**, including 214 internal links, 24 saved model configurations, 11 literature cards, a real edited contact calculation and export, A63 calculations/JSON/PDF, duplicate-click guards, offline disabling, stale/cancelled results and E05 save/import/re-review. The comparison table retains published 590 while displaying reviewed 600. Download feedback and retry are adjacent to Save.

All 37 inline scripts pass syntax checks; six embedded source modules match their files. All 352 referenced hashed assets are intact. Embedded JSON and numerical code are unchanged. Evidence: [UI_NAVIGATION_ACCEPTANCE_20260916.json](UI_NAVIGATION_ACCEPTANCE_20260916.json).

**Evidence limit:** these automated checks exercise the DOM and a real isolated Python API; they do not render pixels. The revised layout is not yet deployed or verified on desktop/phone. The previous screenshots establish baseline workflow outcomes and the need for the fix. After deployment, check the three header routes, Calculate beside the input report, Save beside the solar result, and narrow-screen readability. The broader final-release gates below still apply.


## 2026-09-16: rc4 interface correction

Baseline: `583092071299406f8eaf638ac9cbc30c780b48ee`. Scientific state R139.
The correction remains **1.0.0-rc4**, pending acceptance of the revised interface in a real browser.

Completed against the shipped HTML and an isolated Python service:

- 21 local HTTP, 12 public-mode HTTP and 44 navigation/security checks passed.
- 518 DOM/API assertions passed: all 24 saved local-model configurations, 11 solar literature cards, 211 internal links, core frame-step/play controls, manual fields, JSON imports, input/result/PDF exports, cancellation and rejection of stale results.
- Default contact and edited contact at speed 0.45 were calculated with the real service. A63 was calculated after editing and after entering all parameters by hand.
- Invalid imports preserve the current fields; invalid widths and gamma are reported beside the calculation controls. Unknown inputs remain unknown.
- Inline source modules agree; 37 inline scripts pass syntax checks; all 352 referenced hashed assets are present with the expected bytes. Embedded JSON data and numerical Python implementation are unchanged.

Machine-readable evidence: [UI_ACCEPTANCE_20260916.json](UI_ACCEPTANCE_20260916.json).
The DOM tests use jsdom 26.1.0 and the pinned Python runtime. They record focus/scroll requests and run real API calls. They **do not render the page**.

### Before declaring the final version

On the deployed corrected commit, check desktop and phone:

1. Load a contact, open parameters, set both normal velocities to 0.45, check, calculate and save. The check and calculation must be easy to find below the fields; the answer must show speed 0.45.
2. Open A63, change a bound, calculate, and save JSON/PDF. Also import the saved input. Errors and the next action must be visible without searching the page.
3. Load and edit a solar literature card, review and save/import its draft. Confirm the reference values are distinct from working values and from newly calculated model results.
4. Check vertical field layout on a phone, keyboard focus, image viewers (including the lazy SUVI iframe), PDF/download handling and the www redirect.

Final-release browser acceptance and production load testing are not recorded here. These checks do not establish full MHD branch coverage, global uniqueness, stability or observational identification.

## Historical acceptance, 2026-09-14 (rc3)

The following report is preserved as dated evidence. Its deferred scrolling issue is addressed by the 2026-09-16 correction above; its browser results apply to the earlier deployed code.

# Hosted release-candidate checks

Version: 1.0.0-rc3. Scientific state: R139. Check date: 2026-09-14.

Hosted runtime commit: `3e18e62a628c26df227bdadf2ca3cc5d3f80c24a`.
Application: https://rmo-solar.org/.

These are targeted smoke checks. Browser actions were performed by the maintainer. Exported result files were separately inspected where available. They do not constitute complete browser coverage, a load test, or a new scientific validation campaign.

## Recorded outcomes

| Workflow | Evidence | Outcome |
| --- | --- | --- |
| External link to the deployed landing page | Maintainer browser confirmation after the navigation fix | Page opens |
| A63, bound factor 0.01 | Browser result, input/result JSON comparison, PDF download and inspection | Conditional fast-shock class; input preserved |
| A63 input import and recalculation | Browser confirmation and two exported result files | Imported input retained; exported results agree |
| B01 default contact | Full computed-result JSON inspected | Input VALID; execution FINISHED; two solver calls; 37 independent checks PASS for each of two policies |
| B01 default and edited input in two browser contexts | Full computed-result exports inspected | Normal window retains normal speeds 0.2; incognito uses 0.45 on both sides; returned contact speeds match |
| Brio–Wu saved viewer | Maintainer report | Three saved images displayed; compound-fan download reported |
| Custom-domain TLS | Render statuses copied by maintainer | Apex and www Verified / Certificate Issued; www configured to redirect to apex |
| Custom-domain B01 calculation | Maintainer browser confirmation and two pasted JSON excerpts | Input VALID; shown ENUMERATE_NONREGULAR_1.0 calculation returns 0 without errors; independent validation FINISHED / PASS |

The A63 result files have SHA-256 `fe704db44119c10cf9a380e85d36fc956539adcc5b9bdf81a1285d6189215241`. Byte agreement establishes agreement of exported content; the browser confirmation supplies the evidence of the repeated action.

The normal-window B01 export has SHA-256 `240a30194dee2526680b3db1d468009d4bcb7fa09a82664abe3523136de266a0`. The incognito export has SHA-256 `5273359ab032b5685d3cf35cb138c87408591953dde505cd02527cb756c6d20f`. Their execution identifiers differ, request snapshots and checksums agree, and the recorded source versions are identical. These results demonstrate separation for this two-window test. They do not establish general authorization or isolation properties by themselves; the HTTP regression checks cover those properties within their stated scope.

All 31 source records in the initial hosted B01 export matched the release manifest. The default contact has density 1 on the left and 0.5 on the right; both normal velocities and the checked contact speed are 0.2 in normalized units.

The custom-domain result was available only as excerpts. Its full-file checksum, aggregate execution status, full set of checks and second policy were not independently inspected. The association with the custom domain is the maintainer's report of where the action was performed; the result JSON does not itself authenticate a browser origin.

## Remaining coverage and known interface issue

- A complete manual traversal of all 38 analysis links, every scientific-viewer frame control, lower historical sections and all supported import forms is not documented.
- Direct browser verification of the configured www-to-apex redirect is not separately recorded.
- Load can scroll to the input-check report while Calculate remains above it. Improving that transition is deferred; this release does not change the interface.
- Full MHD branch enumeration, uniqueness, dynamical stability, observational identification and a production load test are not established by these checks.
- The historical UI may retain earlier acceptance wording. This dated report records the current scoped evidence without rewriting scientific records or the interface.

The 21 local HTTP checks, 12 public-mode HTTP checks and 44 navigation regressions remain recorded in `RELEASE_VALIDATION.json`; they were not rerun merely to prepare this documentation. Scientific source and retained results remain unchanged.
