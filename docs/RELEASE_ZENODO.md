# Zenodo release publication

Software version **1.0.0-rc3** is published with DOI [10.5281/zenodo.22741502](https://doi.org/10.5281/zenodo.22741502). The [GitHub release](https://github.com/epodlad/RMO/releases/tag/v1.0.0-rc3) identifies commit `ff6fdf7b289d32b20d4185d57c4e96bbe7a1f40f`. Subsequent DOI/citation documentation updates do not alter that archived tag. The scientific companion remains a separate, pending deposit.

Version 1.0.0-rc3 is a release candidate. The application is hosted at https://rmo-solar.org/. See [release acceptance](RELEASE_ACCEPTANCE.md) for the targeted checks completed on 2026-09-14 and the interactive coverage that remains open. Retain that scope in the release description.

## Software archiving workflow

1. Make the reviewed `epodlad/RMO` repository public in GitHub Settings.
2. Sign in to Zenodo and link the GitHub account. In Zenodo's GitHub settings, sync the repository list and enable `epodlad/RMO`.
3. Create a GitHub release from the prepared commit with tag `v1.0.0-rc3`, title `RMO 1.0.0-rc3 — R139`, and the text in `RELEASE_NOTES.md`. Mark it as a pre-release.
4. After Zenodo processes the release, open the resulting record, verify its archived files, creator, version, license and description, and retain the actual DOI.

See Zenodo's [repository connection](https://help.zenodo.org/docs/github/enable-repository/) and [release archiving](https://help.zenodo.org/docs/github/archive-software/github-upload/) instructions. This route transfers the tagged GitHub source archive directly to Zenodo; downloading and re-uploading the application on a local computer is unnecessary.

Zenodo gives [`.zenodo.json` precedence over `CITATION.cff`](https://help.zenodo.org/docs/github/describe-software/zenodo-json/) for this integration. Both files retain the same creator, software title, version and Apache-2.0 license. Third-party notices remain part of the archive. No DOI or publication date is invented in these files.

## Scientific companion: a separate linked record

Use the already prepared `RMO_science_R139.zip` (1,316,283,163 bytes; SHA-256 `a4d65ddf121bdaa67b5fa75baa2a4fc8abfd5bdd189d6e142085f6a57f648191`). It contains retained scientific data, reproduction code, numerical results, figures, its own manifest and third-party notices. It is not contained in this application repository and will not be transferred by the repository's release webhook.

Deposit the companion separately and describe its scientific scope and source-license distinctions. Link the software and companion records once their actual identifiers are available. Add the software DOI to citation metadata after assignment without altering the already archived tag.

## Manual software fallback

If GitHub integration is not used, create a source ZIP from the exact prepared release commit and deposit it as the software record. The older 69,558,144-byte application ZIP is the pre-navigation-fix baseline and must not be published as the current release. Record the deposited commit and verify the new archive's hash and manifest.

For Software Heritage archival, Zenodo's [manual software-upload guide](https://help.zenodo.org/docs/github/archive-software/manual-upload/) requires a single compressed source-code archive in the software record. Keep the scientific companion separate.
