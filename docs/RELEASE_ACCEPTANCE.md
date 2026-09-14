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
