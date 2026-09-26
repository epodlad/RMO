# Solar-context local MHD fan

One illustrative calibration is supplied: an outer fast shock at750 km/s.
All input plasma states, the normal direction and upstream rest frame are assumptions.
This is not an observational inversion or a unique wave classification.
The one-dimensional ideal-MHD model retains three velocity and magnetic components.
The fan is a connection across the front, not along its visible arc.
A whole extended front may be a single wave surface; it need not contain seven visible ridges.

Use left_right.json for normalized and SI inputs, all_states_physical.csv for the eight
states, wave_table.csv for speeds and manual_energy_fluxes_SI.csv for energy checks.
The outer fast shock connects R1/R0; initial LEFT/RIGHT specify the entire problem.
Gamma=5/3; pure fully ionized hydrogen with Te=Tp; constant normal magnetic field.
A10-degree transverse-field rotation is assumed. Other inputs can change the wave content.

Run python -B examples/solar20170910_full_fan/run.py to recompute, or
python -B examples/solar20170910_full_fan/check_conservation.py for independent scalar checks.
The search time budget is not the physical model age. No exhaustive uniqueness is claimed.
At1024 and2048 cells a separate MUSCL-MC/HLL/SSP-RK2 evolution at60s gives maximum
scaled mean primitive errors0.001804 and0.000898; the finer-grid conservation residual
is6.87e-14. Such checks verify the model, not its observational correspondence.

Solar context: public NOAA/NCEI SUVI observations and Veronig et al.(2018),
DOI10.3847/1538-4357/aaeac5. Radiance is not a direct density or magnetic-field measurement.
