# Render deployment

The service uses Render's native Python runtime. The large scientific companion is not required at build or runtime.

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

The included [Blueprint](../render.yaml) declares these settings. The A63/B01 smoke workload in [release validation](../RELEASE_VALIDATION.json) is not a load test or a guarantee for every traffic pattern.

The server binds to `0.0.0.0` and uses Render's `PORT`. It obtains its default HTTPS origin from `RENDER_EXTERNAL_URL`. Render terminates TLS. These behaviors follow the official [web-service documentation](https://render.com/docs/web-services), [environment-variable reference](https://render.com/docs/environment-variables), [Python-version settings](https://render.com/docs/python-version) and [Blueprint specification](https://render.com/docs/blueprint-spec).

The public application is [rmo-solar.org](https://rmo-solar.org/), with HTTPS and a www-to-apex redirect. The allowed custom origin is configured with `RMO_PUBLIC_ORIGINS=https://rmo-solar.org`. Additional origins must match hostnames actually served by the deployment; Host and origin checks remain enabled.

Recorded application checks and remaining coverage are summarized in [release verification](RELEASE_ACCEPTANCE.md).

Keep one instance and one application process: calculation capacity and session state are maintained in that process. Session expiry or a restart requires a page reload. A busy response asks the visitor to retry after the active calculation. Public results are not written to a shared result directory.
