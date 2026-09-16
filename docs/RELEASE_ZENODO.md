# Publication of the rc4 interface correction

The published software rc4 record is [10.5281/zenodo.22776018](https://doi.org/10.5281/zenodo.22776018), published 2026-09-15. The existing rc3 DOI [10.5281/zenodo.22741502](https://doi.org/10.5281/zenodo.22741502) remains valid for citations to that version. The scientific companion R139 remains [10.5281/zenodo.22742107](https://doi.org/10.5281/zenodo.22742107).

The maintainer requested **no new DOI** for this interface correction. Keep version `1.0.0-rc4`; publishing a new GitHub release while its Zenodo integration is enabled can initiate a new archive. A commit to main and a Render deployment are separate from creating a GitHub release.

## Current correction workflow

1. Apply the complete reviewed delta to the repository root and commit the files. Do not upload an extra wrapper `files/` directory. The updater checks baseline hashes and can create a backup before copying changes.
2. Deploy that commit on Render and perform the browser checks in `RELEASE_ACCEPTANCE.md`. [Render manual deploy documentation](https://render.com/docs/deploys#manual-deploys).
3. For this minor interface correction, open the existing rc4 Zenodo record. Under **Edit files**, choose **Edit published files** and follow its correction dialog. Upload the full corrected application source archive in place of the software archive. The delta ZIP alone is not a complete software deposit.
4. Keep the version and DOI; add a dated correction note describing the interface changes, the automated checks, and browser acceptance evidence actually completed. Record the GitHub correction commit and the archive SHA-256. Preserve licenses and the historical scientific scope.
5. Publish the correction draft and verify the same DOI, intended archive, metadata and downloads. This package preparation does not itself perform that publication.

Zenodo permits minor file corrections within 30 days of original publication. Its correction draft must be published within 45 days of the original publication; this route retains the DOI. If this route is unavailable or Zenodo determines that the change requires a new version, stop and resolve the publication choice rather than replacing a different record. [Zenodo file-correction documentation](https://help.zenodo.org/docs/deposit/manage-files/#modify-files-after-publication).

Do not replace the cited rc3 archive with rc4, retag the published rc4 source, or change the separate R139 deposit as part of this correction. The GitHub rc4 tag continues to identify its original snapshot; the dated correction commit and archive manifest identify the corrected source.

## Final 1.0.0 release

A final version requires acceptance of the corrected hosted interface. A new final release and archiving policy must then be decided explicitly while respecting the maintainer's no-new-DOI constraint. This package does not declare full production acceptance or create a new release/DOI.
