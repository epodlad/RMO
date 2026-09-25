"""Check all seven conserved fluxes at six discontinuities, without RMO imports."""
from pathlib import Path
import csv
import json
import math

HERE = Path(__file__).resolve().parent
GAMMA = 5 / 3
MU0 = 4e-7 * math.pi


def flux(row, speed):
    rho, p = float(row['rho_kg_m3']), float(row['p_Pa'])
    un, uy, uz = [1000 * float(row[k]) for k in ('un_km_s', 'ut1_km_s', 'ut2_km_s')]
    bn, by, bz = [1e-4 * float(row[k]) for k in ('Bn_G', 'Bt1_G', 'Bt2_G')]
    b2 = bn*bn + by*by + bz*bz
    energy = p/(GAMMA-1) + rho*(un*un+uy*uy+uz*uz)/2 + b2/(2*MU0)
    total_p = p + b2/(2*MU0)
    mass = rho*(un-speed)
    return [mass, mass*un+total_p-bn*bn/MU0, mass*uy-bn*by/MU0,
            mass*uz-bn*bz/MU0, (un-speed)*by-bn*uy, (un-speed)*bz-bn*uz,
            (un-speed)*energy+un*total_p-bn*(un*bn+uy*by+uz*bz)/MU0]


def main():
    states = list(csv.DictReader((HERE/'all_states_physical.csv').open()))
    waves = list(csv.DictReader((HERE/'wave_table.csv').open()))
    norm = json.loads((HERE/'left_right.json').read_text())['normalization']
    rho, v, p, b = [norm[k] for k in ('density_kg_m3','velocity_m_s','pressure_Pa','magnetic_field_T')]
    scales = [rho*v, p, p, p, b*v, b*v, p*v]
    checks = []
    for i, wave in enumerate(waves):
        if wave['structure'] == 'rarefaction':
            continue
        speed = 1000*float(wave['speed_left_km_s'])
        a, z = flux(states[i], speed), flux(states[i+1], speed)
        residual = max(abs(y-x)/max(abs(x),abs(y),s) for x,y,s in zip(a,z,scales))
        bn_error = abs(float(states[i]['Bn_G'])-float(states[i+1]['Bn_G']))
        assert residual < 1e-10 and bn_error < 1e-12, wave['family']
        checks.append({'wave':i+1,'family':wave['family'],'max_scaled_flux_residual':residual,
                       'energy_flux_left_W_m2':a[-1],'energy_flux_right_W_m2':z[-1]})
    print(json.dumps({'interpretation':'Conservation check for supplied model states; not an observational identification',
                      'boundaries_checked':len(checks),'checks':checks,
                      'scope':'Rarefaction requires a continuous wave-curve check. Shock entropy and characteristics are separate admissibility checks.'},indent=2))


if __name__ == '__main__':
    main()
