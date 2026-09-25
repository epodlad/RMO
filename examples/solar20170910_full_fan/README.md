# Solar 2017 September 10: assumed local full MHD fan

This saved example gives seven nonzero wave families for explicit assumed initial states.
The solar image and proposed windows are observational context, not recovered plasma states.
Across the outer fast shock compare R1 and R0. Initial LEFT=L0 and RIGHT=R0 define the whole fan.

Inputs: left_right.json. State, wave and direct energy-flux tables are included.
Gamma=5/3; normalized mu0=1; SI conversion and energy convention are in the JSON.
The computational normal has not yet been assigned a unique heliographic direction.
Radiance alone does not determine the plasma flow or coronal magnetic vector.

Numerical controls found a fast shock near 940.038 km/s, compression 1.661738 and Mf=1.522844.
An independent HLL finite-volume implementation reproduced the fan with decreasing grid error.
The 10-degree transverse-field rotation is assumed; a coplanar control has zero rotational amplitudes.
The weak right slow branch changes from shock to rarefaction for other plausible assumed left states.
This is a full model fan, not a uniqueness claim or a complete observational inversion.

Sources: Veronig et al. 2018 (10.3847/1538-4357/aaeac5), Long et al. 2018
(10.3847/1538-4357/aaad68), and NOAA/NCEI GOES-16 SUVI L1b 195 A public files.
Native 2017 SUVI RSUN_OBS is in pixels; CROTA is used for solar orientation.

Recompute with `python examples/solar20170910_full_fan/run.py`.
For the alternative, add `--input examples/solar20170910_full_fan/alternative_slow_rarefaction.json`.
The runtime limit is a numerical search budget, not a model age.
A failed or incomplete search does not establish physical nonexistence.

Check the supplied discontinuities without importing RMO:
`python examples/solar20170910_full_fan/check_conservation.py`.
This substitutes each adjacent pair into all seven conservative flux equations.
The continuous rarefaction, shock entropy and characteristic admissibility require separate checks.
