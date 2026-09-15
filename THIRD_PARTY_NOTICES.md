# Third-party notices and source acknowledgements

Apache-2.0 applies to original RMO code. It does not replace the terms of third-party software, fonts, published works or observational data. Scientific citations identify the original investigators; they do not imply their endorsement of RMO's conditional interpretations.

## Distributed software and fonts

- The Aegir reference attribution and MIT license are retained at `implementation/reference/aegir_975cc7ed/LICENSE`, including Neco Kriel's copyright notice.
- DejaVu Sans fonts and their full license are retained in `uncertainty_diagnosis/fonts/`. The font license is independent of Apache-2.0.
- Python dependencies are installed from their upstream distributions using `requirements.txt`. Their upstream license files remain part of those installed distributions. RMO does not relicense NumPy, SciPy, PyYAML, ReportLab, pypdf, Pillow, charset-normalizer or aiohttp and its dependencies.
- Scientific reproduction may additionally require the versions recorded in the scientific companion's per-study runtime records. Bundled CHIANTI atomic data retain their source identity and acknowledgement requirements. ChiantiPy's historical vendor installation is not redistributed.

## Observational data and RMO figures

SDO/AIA data and figures calculated from those data retain the credit: Courtesy of NASA/SDO and the AIA, EVE, and HMI science teams. See the [SDO use policy](https://sdo.gsfc.nasa.gov/gallery/copyright/) and [NASA media guidance](https://www.nasa.gov/nasa-brand-center/images-and-media/). Original observation identifiers, times, channels and processing assumptions remain in the scientific records.

Hinode/EIS observations retain Hinode, ISAS/JAXA, NAOJ, NASA, STFC, ESA and NSC mission acknowledgements. Refer to the [Hinode data policy](https://hinode.msfc.nasa.gov/data.html), [ISAS research-data policy](https://www.isas.jaxa.jp/en/researchers/data-policy/) and [EIS acknowledgement guidance](https://solarb.mssl.ucl.ac.uk/SolarB/Acknowledgements.jsp).

STEREO/SECCHI, IRIS and Solar Orbiter/SWA records retain their source/provider and instrument-team citations in the companion. Consult the [IRIS archive](https://jsoc.stanford.edu/IRIS/IRIS.html) and [Solar Orbiter publication acknowledgements](https://www.cosmos.esa.int/web/solar-orbiter/solar-orbiter-publication-acknowledgement). CHIANTI users should cite the database and relevant atomic-data publications as described by [CHIANTI](https://www.chiantidatabase.org/).

RMO-generated plots are derived scientific visualizations, not new observations. The existing RMO logo is artwork, not an observational image. Standard content-credential signatures on retained historical figures remain intact.

## Restored GOES-16/SUVI preview

The 10 September 2017 preview uses NOAA/GOES-16 SUVI 195 Å imagery, credited to **NOAA SWPC** on the [official NOAA source page](https://www.goes-r.gov/multimedia/dataAndImageryVideosGoes-16.html). The 51 cropped/resized JPEG frames correspond, in order, to video frames 0, 2, …, 100 of the [official animation](https://www.goes-r.gov/multimedia/originalVideoCopies/dataAndImagery/GOES16/suvi_195_dynamic_20170910.mp4). The original download route is not established; the frames are not attributed to Helioviewer.

The original JPEGs, saved display-difference images and comparison MP4 are restored without changing their bytes. RMO produced the displayed differences and ratios of rendered brightness. These are visual previews, not calibrated intensity measurements or a shock classification. The source comparison and asset hashes are recorded in [SUVI media provenance](docs/SUVI_MEDIA_PROVENANCE.json).

[NOAA's image and video guidance](https://www.omao.noaa.gov/image-licensing-usage-info) permits educational and informational reuse, including webpages. NOAA imagery remains separate from the Apache-2.0 license on RMO code; credit does not imply NOAA endorsement. For detailed scientific observations and processing, cite [Seaton and Darnel (2018)](https://doi.org/10.3847/2041-8213/aaa28e).

## Source-linked material

The following published figures or composites are referenced through their sources rather than distributed in this release:

| Source | Referenced material |
| --- | --- |
| [Veronig et al. (2011)](https://doi.org/10.1088/2041-8205/743/1/L10) | Published crossing and EIS-trace images, including composites |
| [Liu et al. (2012)](https://doi.org/10.1088/0004-637X/753/1/52) | Published tracking figure |
| [Ma et al. (2011)](https://arxiv.org/abs/1106.6056) | Published photometry-box panels used in source/patch composites |
| [Ye et al. (2026)](https://doi.org/10.1038/s41467-026-75039-z) | Published Figure 4 and original Source Data workbook |

The Ye et al. publisher page specifies CC BY-NC-ND 4.0. The original workbook is obtained directly from the publisher for local reproduction. It is not incorporated into RMO's Apache-licensed distribution. The retained numerical profile records and independently calculated RMO results carry the original scientific citation; they are not presented as measurements acquired by RMO.

Full texts of third-party articles and unverified source media are not part of the release. No substitute observational imagery has been fabricated.
