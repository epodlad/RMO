# Connected front interaction

Open **Explore a front interaction** at the top of RMO QuickLook. The time slider displays a saved dimensionless MHD solution before and after two incoming shocks meet. Both JSON exports are available inside the example.

This is a constructed ideal-MHD example, not a reconstruction of measured solar plasma. Initially LEFT, MIDDLE and RIGHT are separated at x = -1 and 0. The incoming fast shock overtakes the slow shock; the new Riemann problem uses the unchanged external LEFT and RIGHT states. All seven regular wave families are available to the solver. The resulting weak fast/slow rarefactions and contact are computed, while the two rotational amplitudes vanish for these coplanar inputs.

## Reproduce

From the repository root, with the project dependencies installed:

```sh
python3 -B examples/front_interaction/run.py
```

The script writes its solution and finite-volume comparison into `examples/front_interaction/results/`. Portable input is in `examples/front_interaction/solver_input.json`. Use its three-state problem to evolve through collision, or its two-state LEFT/RIGHT problem with the origin shifted to the collision. Units have mu0 = 1 and gamma = 5/3; the first vector component is normal.

## Physical checks and scope

The example checks conserved fluxes F - D U, constant normal magnetic field, shock entropy production, strict Lax inequalities, contact matching and continuous isentropic rarefaction curves. A separate HLL/MUSCL/SSPRK2 implementation evolves the three-state initial data through collision. Its maximum mean primitive error falls from 3.36e-4 to 1.80e-4 on 1200 and 2400 cells. These grids check the bulk profile; they do not separately resolve the tiny contact and narrow rarefaction widths.

One regular root is recovered in the base and doubled finite search. The exported `complete: false` remains important: this is not exhaustive enumeration of intermediate shocks, compound waves or degenerate branches. No external community solver comparison is claimed. The example uses ideal isotropic MHD without gravity, conduction or a continuing driver.

For a shock, check the entropy change along the mass flow. A contact can have different specific entropy on its sides with zero entropy production because its normal mass flux is zero. A rarefaction is checked along its continuous wave curve, not as a single shock between endpoints.

Reference for the MHD Riemann wave families and regular/nonregular distinction: [Takahashi & Yamada (2014)](https://arxiv.org/abs/1310.2330).
