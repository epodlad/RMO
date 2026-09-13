# Zenodo release preparation

This package is a release candidate. Complete the browser/hosted checks in `DEPLOY_RENDER.md` before public publication. The private repository can remain private while an explicitly selected release archive is deposited in Zenodo.

Use two linked records:

1. **Software:** `RMO_application_1.0.0-rc3.zip`, containing the application source, reviewed assets, licenses, citation metadata and validation report. Use the prepared title, creator, version and description in `.zenodo.json`.
2. **Scientific companion:** `RMO_science_R139.zip`, containing retained scientific data, reproduction code, numerical results, figures and its own file manifest. Describe it as the scientific companion to this software version and retain its third-party notices.

Link the two records after their identifiers are available, and add the resulting software DOI to `CITATION.cff` and `.zenodo.json`. A DOI has not been reserved or invented in this package. Record the actual publication date only when publishing. Cite the repository commit identifying the exact deposited software version.

For Software Heritage archival, Zenodo's [manual software-upload guide](https://help.zenodo.org/docs/github/archive-software/manual-upload/) requires a single compressed source-code archive in the software record. This is why the scientific companion has a separate record. The [Zenodo metadata documentation](https://help.zenodo.org/docs/github/describe-software/zenodo-json/) also explains that `.zenodo.json` takes precedence over `CITATION.cff` in GitHub-based archiving.

Verify the archive hashes against `SHA256SUMS.txt` before upload. Review the author name and metadata as ordinary release metadata, preserve third-party license distinctions, and publish only the selected release packages. Neither a software commit nor this preparation creates a public Zenodo deposit automatically.
