# Render deployment

The prepared service uses Render's native Python runtime. The large scientific companion is not required at build or runtime.

| Setting | Value |
| --- | --- |
| Repository | `epodlad/RMO` |
| Branch | `main` |
| Root directory | Repository root |
| Runtime | Python |
| Python version | `3.12.14` |
| Build command | `python -m pip install -r requirements.txt` |
| Start command | `python -B -m web_app.server` |
| Health check | `/healthz` |
| Instances | `1` |
| Automatic deployment | Off |
| Initial compute configuration | `0.5c-512mb` |
| Persistent disk | None |

The included Blueprint declares these settings. Review the current plan price in Render before creating a paid service. The measured A63/B01 smoke workload is recorded in `RELEASE_VALIDATION.json`; it is not a load test or a guarantee for every traffic pattern.

The server binds to `0.0.0.0` and uses Render's `PORT`. It obtains its default HTTPS origin from `RENDER_EXTERNAL_URL`. Render terminates TLS. These behaviors follow the official [web-service documentation](https://render.com/docs/web-services), [environment-variable reference](https://render.com/docs/environment-variables), [Python-version settings](https://render.com/docs/python-version) and [Blueprint specification](https://render.com/docs/blueprint-spec).

After the initial `onrender.com` service works, add `rmo-solar.org` in Render's Custom Domains settings. Apply the DNS records shown for that service, then wait for domain verification and its certificate. Set `RMO_PUBLIC_ORIGINS=https://rmo-solar.org` and restart the service. Add another origin only if that exact HTTPS hostname is actually served. Do not guess the service's DNS target or disable Host/origin checks.

Before accepting a hosted release, check the public HTTPS address in a browser: page layout and all 38 analysis links; A63 input → Python → result → PDF; input/result JSON downloads; B01; supported import forms; scientific viewer frame changes; collapsed scientific evidence and lower history; two independent browser sessions. For the restored 2017 media, open the header example, check Play/Pause and frame stepping, close and reopen at frame 23, and check the event-card still and comparison video. The preview must load inside the page; its source and scientific-reference links are supplementary.

Keep one instance and one application process: calculation capacity and session state are maintained in that process. Session expiry or a restart requires a page reload. A busy response asks the visitor to retry after the active calculation. Public results are not written to a shared result directory.
