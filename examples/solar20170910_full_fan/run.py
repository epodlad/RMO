"""Recompute the assumed solar-context example with the RMO regular-fan solver."""
from pathlib import Path
import argparse,json,sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'implementation'))
from rmo.models import State
from rmo.regular_fan import search_regular_fans_stabilized

def state(values,label):
    rho,p,un,ut1,ut2,bn,bt1,bt2=values
    return State(rho,p,(un,ut1,ut2),(bn,bt1,bt2),id=label)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=HERE/'left_right.json')
    parser.add_argument('--output',type=Path,default=HERE/'recomputed_fan.json')
    parser.add_argument('--seconds',type=float,default=60.)
    args=parser.parse_args();data=json.loads(args.input.read_text())
    L=state(data['states']['LEFT']['primitive_normalized'],'LEFT')
    R=state(data['states']['RIGHT']['primitive_normalized'],'RIGHT')
    result=search_regular_fans_stabilized(L,R,data['gamma'],base_starts=4,wall_time_seconds=args.seconds)
    out={'case':data['case'],'interpretation':'ASSUMED_MODEL; not an observational inversion',
         'left':L.serializable(),'right':R.serializable(),'gamma':data['gamma'],
         'solutions':[s.serializable() for s in result.solutions],
         'root_set_stable':result.root_set_stable,'complete':result.complete,
         'domain_codes':list(result.domain_codes),'starts_attempted':result.starts_attempted}
    args.output.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'solutions':len(result.solutions),'root_set_stable':result.root_set_stable,'complete':result.complete}))

if __name__=='__main__':main()
