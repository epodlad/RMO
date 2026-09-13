"""Independent Decimal-precision local checks; NOT an all-branch solver.

Only the standard library is required. Decimal precision controls rounding;
RK4 refinement separately estimates ODE truncation. Input decimal precision
does not increase merely because the arithmetic uses more digits.
"""
import json
import time
from decimal import Decimal, localcontext

def D(x): return Decimal(str(x))

def read_solution(path):
    return json.loads(path.read_text(),parse_float=str)

def state(r):
    return [D(r['rho']),D(r['p']),*map(D,r['u']),*map(D,r['B'])]

def state_map(solution):
    result={r['id']:r for r in solution['intermediate_states']}
    result['X_L0']=solution['initial_left'];result['X_R0']=solution['initial_right']
    return result

def speeds(a,gamma):
    rho,p,un,uy,uz,bn,by,bz=a
    sound2=gamma*p/rho; b2=bn*bn+by*by+bz*bz; total=sound2+b2/rho
    cf2=(total+(total*total-4*sound2*bn*bn/rho).sqrt())/2
    return cf2.sqrt(),abs(bn)/rho.sqrt(),(sound2*bn*bn/(rho*cf2)).sqrt()

def conserved_flux(a,gamma):
    rho,p,un,uy,uz,bn,by,bz=a; b2=bn*bn+by*by+bz*bz
    energy=p/(gamma-1)+rho*(un*un+uy*uy+uz*uz)/2+b2/2
    conserved=[rho,rho*un,rho*uy,rho*uz,by,bz,energy]
    flux=[rho*un,rho*un*un+p+b2/2-bn*bn,rho*un*uy-bn*by,
          rho*un*uz-bn*bz,un*by-bn*uy,un*bz-bn*uz,
          (energy+p+b2/2)*un-bn*(bn*un+by*uy+bz*uz)]
    return conserved,flux

def residual(a,b,s,gamma):
    qa,fa=conserved_flux(a,gamma);qb,fb=conserved_flux(b,gamma)
    raw=[y-x-s*(v-u) for x,y,u,v in zip(fa,fb,qa,qb)]
    scale=[max(D(1),abs(x),abs(y),abs(s*u),abs(s*v)) for x,y,u,v in zip(fa,fb,qa,qb)]
    return max(abs(x)/w for x,w in zip(raw,scale)),raw

def flux_checks(solution,gamma,dps):
    with localcontext() as ctx:
        ctx.prec=dps;g=D(gamma);states=state_map(solution);checks=[]
        for w in solution['waves']:
            if isinstance(w['speed'],list):continue
            a,b=state(states[w['left_state_ref']]),state(states[w['right_state_ref']])
            error,raw=residual(a,b,D(w['speed']),g)
            checks.append({'order':w['order'],'structure':w['structure'],'scaled_RH':str(error),
                           'raw_residuals':list(map(str,raw))})
        return {'decimal_digits':dps,'checks':checks,'max_RH':max(float(v['scaled_RH']) for v in checks),
                'scope':'supplied_decimal_state_residuals_not_new_input_precision'}

def linear_solve(a,b):
    n=len(b);rows=[list(row)+[rhs] for row,rhs in zip(a,b)]
    for k in range(n):
        pivot=max(range(k,n),key=lambda i:abs(rows[i][k]));rows[k],rows[pivot]=rows[pivot],rows[k]
        if abs(rows[k][k])<D('1e-40'):raise ValueError('SINGULAR_PRECISION_JACOBIAN')
        d=rows[k][k];rows[k]=[v/d for v in rows[k]]
        for i in range(n):
            if i==k:continue
            f=rows[i][k];rows[i]=[v-f*w for v,w in zip(rows[i],rows[k])]
    return [row[-1] for row in rows]

def rarefaction_endpoint(up_record,down_record,gamma,family,direction,dps=40,steps=512,budget=None):
    began=time.monotonic()
    with localcontext() as ctx:
        ctx.prec=dps;up=state(up_record);expected=state(down_record);g=D(gamma)
        rho0,p0,un0,uy0,uz0,bn,by0,bz0=up
        if abs(bz0)>D('1e-12') or abs(uz0)>D('1e-12'):
            raise ValueError('NONCOPLANAR_PRECISION_CHECK_UNSUPPORTED')
        target=-(expected[0]/rho0).ln()
        if target<0:raise ValueError('NOT_AN_EXPANSION')
        def rhs(z,y):
            if budget:budget.check()
            rho=rho0*(-z).exp();p=p0*(-g*z).exp();un,uy,by=y
            c=speeds([rho,p,un,uy,D(0),bn,by,D(0)],g)[0 if family=='fast' else 2]
            du=-direction*c
            dv,db=linear_solve([[-direction*rho*c,-bn],[-bn,-direction*c]],[D(0),-by*du])
            return [du,dv,db]
        y=[un0,uy0,by0];h=target/steps
        for i in range(steps):
            z=i*h;k1=rhs(z,y)
            k2=rhs(z+h/2,[a+h*b/2 for a,b in zip(y,k1)])
            k3=rhs(z+h/2,[a+h*b/2 for a,b in zip(y,k2)])
            k4=rhs(z+h,[a+h*b for a,b in zip(y,k3)])
            y=[a+h*(b+2*c+2*d+e)/6 for a,b,c,d,e in zip(y,k1,k2,k3,k4)]
        un,uy,by=y;found=[expected[0],p0*(-g*target).exp(),un,uy,D(0),bn,by,D(0)]
        error=max(abs(a-b)/max(1,abs(a),abs(b)) for a,b in zip(found,expected))
        return {'method':'Decimal_RK4_log_density','decimal_digits':dps,'steps':steps,
                'conditional_input':'upstream_state_and_downstream_density','state':list(map(str,found)),
                'max_relative_state_error':float(error),'wall_seconds':time.monotonic()-began}

def shock_endpoint(up_record,down_record,speed,gamma,dps=50,budget=None):
    with localcontext() as ctx:
        ctx.prec=dps;up=state(up_record);expected=state(down_record);g=D(gamma)
        rho=expected[0];bn=up[5]
        def equations(values):
            if budget:budget.check()
            p,un,uy,by,s=values
            _,raw=residual(up,[rho,p,un,uy,D(0),bn,by,D(0)],s,g)
            return [raw[i] for i in (0,1,2,4,6)]
        values=[expected[1]*D('1.001'),expected[2]+D('.0001'),expected[3]-D('.0001'),
                expected[6]*D('1.001'),D(speed)+D('.0001')]
        for it in range(25):
            r=equations(values)
            if max(map(abs,r))<D('1e-35'):break
            columns=[]
            for j in range(5):
                step=D('1e-12')*max(1,abs(values[j]));a=values.copy();b=values.copy();a[j]+=step;b[j]-=step
                columns.append([(x-y)/(2*step) for x,y in zip(equations(a),equations(b))])
            delta=linear_solve([list(row) for row in zip(*columns)],[-v for v in r])
            values=[a+b for a,b in zip(values,delta)]
        else:raise ValueError('PRECISION_SHOCK_NOT_CONVERGED')
        p,un,uy,by,s=values;found=[rho,p,un,uy,D(0),bn,by,D(0)]
        error=max(abs(a-b)/max(1,abs(a),abs(b)) for a,b in zip(found,expected));err,_=residual(up,found,s,g)
        return {'method':'Decimal_Newton_five_conserved_flux_equations','decimal_digits':dps,'iterations':it,
                'conditional_input':'upstream_state_and_downstream_density; perturbed_stored_state_as_local_seed',
                'state':list(map(str,found)),'speed':str(s),'max_relative_state_error':float(error),
                'reconstructed_RH':str(err),'max_relative_speed_error':float(abs(s-D(speed))/max(1,abs(s),abs(D(speed))))}
