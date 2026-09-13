# RMO-75: bounded local diagnosis protocol

Frozen before executing the study. User authorization: continue the uncertainty
checks and connect the checked diagnosis to QuickLook. Earlier results are retained.

## Question and claim

For an already checked single planar ideal-MHD discontinuity, do strict fast/slow
characteristic ordering, compression, entropy increase and transverse-field trend
survive every state in a supplied measurement box? A certificate is **conditional
on the single-discontinuity model and on conservation**. It is neither an EUV-image
classification nor a proof of full Riemann-fan uniqueness or dynamical stability.

Two separate outputs are required: (1) nominal-state conservation and local class,
(2) sufficient interval bounds on shock-family inequalities. Only a nominal pair
passing the existing conservation checks can anchor a reported conditional robust
class. No noisy pair is silently projected onto an exact solution. Failure of a
sufficient bound means NOT CERTIFIED, not proof of two feasible competing solutions.
An independent Decimal calculation verifies conservation and characteristics of
the anchor, and is exposed in the response.

## Method

Use 50-digit Decimal intervals with outward expansion after every arithmetic
operation. Enclose fast, normal-Alfven and slow speeds, front-relative normal flow,
density ratio, entropy change, transverse-field magnitude and alignment. Require
all relevant lower margins to be strictly positive. Keep the normal magnetic field
and front speed shared between sides. The enclosing box may include additional
unphysical combinations; this makes the sufficient test conservative. Normal
geometry and gamma are fixed model settings; neither is measured by this exercise.
Covariance probabilities, fitting and posterior confidence are not implemented.

Contact and rotational discontinuities require equalities. A free measurement box
does not certify these equalities; retain their checked nominal diagnosis and mark
finite-error classification not certified. Missing input stays unknown. Do not use
zero or an assumed coronal average to fill a missing observable.

## Frozen design

Use anonymous development inputs A17, A42, A63, A88 without passing their expected
labels. Reuse their separate historical reference only for scoring. Test half-width
factors f = 0, .01, .05, .10. For density/pressure use f*abs(value); for every velocity,
field component and front speed use f*max(1,abs(value)) in the normalized frame.
This includes nonzero uncertainty at zero components. These are illustrative
bounded errors, not one-sigma errors or estimates from an instrument. Test missing
front speed, missing field and missing pressure. Check shared Galilean offsets,
normal reversal, invalid bounds, nominal conservation failure, and independent
high-precision enclosure checks on a deterministic sample of box points. Sampling
tests implementation only; the certificate is based on interval bounds, not samples.

## Observational application

Use the already transcribed Podladchikova et al. (2019) Tables 4-5, same selected
patch as confirmed by the user. Recalculate geometric speed differences. State
explicitly which inputs for this local classifier are absent. No new observational
downloads, solar classification from the paper's label, or assumed field/temperature.

## Integration boundary

Keep the existing Riemann solver and its restricted special-case API intact. Add a
separate Python local-discontinuity diagnosis action, with request identity, retained
input/result, stale-result protection and an input export/import path. Offline HTML
can show the saved study and export edited requests; fresh Python calculation needs
the existing local service. No public deployment and no native-browser claim.

## Pilot refinement before the final study

Initial interval evaluation showed dependency overestimation in cf-ca and ca-cs.
Use the exact magnetosonic-polynomial identity P(ca^2) = -ca^2 Bt^2/rho < 0
to establish strict ordering when rho,p,Bn^2,Bt^2 are bounded away from zero.
Do not tune widths to obtain a desired outcome.

For noisy nominal states, add a limited feasible-state search inside the *unchanged*
input box, using bounded least-squares of conservation alone with at most 400
evaluations from the centre. No family label or saved fixture is provided. A found
point must pass the independent Decimal conservation check and the original local
classifier. It is a numerical witness at stated tolerance, not a best estimate,
posterior or unique reconstruction. Failure to find one is SEARCH_INCOMPLETE,
not physical exclusion. A robust certificate still requires whole-box sufficient
inequalities, not just the fitted point. Record every adjustment and the search
termination. Deterministic noisy-centre controls must contain the original exact
state and must not pass the tight nominal conservation check.
