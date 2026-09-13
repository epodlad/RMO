"""Vector single-result PDF for the local diagnostic response."""
from io import BytesIO
import hashlib
import json
import textwrap
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor

def make_pdf(req,out):
    fonts=Path(__file__).resolve().parent/'fonts'
    for name,file in [('RMOText','DejaVuSans.ttf'),('RMOBold','DejaVuSans-Bold.ttf')]:
        if name not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(name,str(fonts/file)))
    buffer=BytesIO();c=Canvas(buffer,pagesize=(595,842),invariant=1)
    c.setTitle('RMO - local diagnosis and input bounds')
    c.setAuthor('RMO research prototype')
    c.setFillColor(HexColor('#183538'));c.setFont('RMOBold',22)
    c.drawString(42,792,'RMO | local MHD diagnosis')
    version=('RMO-82 / conservation-coupled' if out.get('integration')=='RMO81-conservation-coupled-perpendicular' else
             'RMO-79' if out.get('integration')=='RMO79-fixed-perpendicular-bounds' else
             'RMO-78' if out.get('integration')=='RMO78-exact-perpendicular' else 'RMO-75')
    c.setFont('RMOText',10);c.drawString(42,773,'One planar discontinuity - normalized units - '+version)
    y=744
    def para(text,size=10):
        nonlocal y
        c.setFont('RMOText',size)
        for line in textwrap.wrap(str(text),width=92 if size==10 else 106):
            c.drawString(42,y,line);y-=14
        y-=8
    para(out['status'])
    para(out['result_sentence'])
    if out.get('integration') in ['RMO79-fixed-perpendicular-bounds','RMO81-conservation-coupled-perpendicular']:
        para('Fixed model constraint: B_n = 0 with zero width. The field lies along the front surface. Other values retain their supplied bounds; this is not an uncertain-angle test.',9)
    nominal=out.get('nominal',{})
    para('Nominal exact-state check: '+nominal.get('status','not evaluated'))
    audit=out.get('independent_check',{})
    para('Independent nominal conservation: '+audit.get('status','not evaluated')+
         '; scaled residual '+(format(float(audit['rh_scaled_inf']),'.3g') if 'rh_scaled_inf' in audit else 'not reported'))
    if out.get('joint_entropy_check'):
        v=out['joint_entropy_check']['bounds']
        para('Conservation-linked entropy / c_v: ['+format(v[0],'.6g')+', '+format(v[1],'.6g')+']. Applies to RH-compatible states in the supplied ranges.',9)
    if out.get('witness'):
        para('Conservation witness: '+out['witness']['independent_check']['status']+
             '. Adjustments are retained in the JSON. This point is not a best estimate.')
    points=out.get('plot_kind')=='nominal_points'
    bounds=({s:{k:[v,v] for k,v in rows.items()} for s,rows in out['characteristic_values'].items()} if points else out.get('characteristic_bounds'))
    flow=({s:[v,v] for s,v in out['relative_speed_values'].items()} if points else out.get('relative_speed_bounds'))
    if bounds and flow:
        rows=[]
        for side in ('left','right'):
            for key in ('slow','alfven_n','fast'):rows.append((side+' '+key,bounds[side][key],key))
            v=flow[side];rows.append((side+' |u_n - S|',[0 if v[0]<=0<=v[1] else min(map(abs,v)),max(map(abs,v))],'flow'))
        vmax=max(v[1] for _,v,_ in rows)*1.08 or 1
        x0,x1=204,550
        for name,v,key in rows:
            c.setFillColor(HexColor('#183538'));c.setFont('RMOText',9);c.drawString(42,y-3,name)
            colour={'slow':'#247668','alfven_n':'#80519a','fast':'#287dab','flow':'#222222'}[key]
            c.setStrokeColor(HexColor(colour));c.setFillColor(HexColor(colour));c.setLineWidth(3)
            a=x0+v[0]/vmax*(x1-x0);b=x0+v[1]/vmax*(x1-x0)
            c.line(a,y,b,y);c.circle((a+b)/2,y,2,fill=1,stroke=0);y-=24
        c.setFillColor(HexColor('#183538'));c.setFont('RMOText',8)
        for i in range(5):c.drawCentredString(x0+i*(x1-x0)/4,y,str(round(vmax*i/4,3)))
        y-=22;para('Evaluated model speeds and front-relative flow. Points are not observational error bars.' if points else 'Characteristic-speed enclosures and front-relative flow. Bars are bounded ranges, not standard deviations.',9)
    para('Next: '+out['next_action'])
    para('Exact conservation equalities are sensitive to measurement errors. Classification robustness is a separate test. A failed sufficient bound does not prove another feasible solution.',9)
    para('Conditional on the stated model, fixed geometry and gamma. No global Riemann uniqueness, dynamical stability or observed EUV identification is claimed.',9)
    digest=hashlib.sha256(json.dumps(req,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    c.setFont('RMOText',7);c.drawString(42,43,'Canonical input SHA-256: '+digest)
    c.drawString(42,30,'Save the request/result JSON for complete values, bounds and witness adjustments.')
    c.showPage();c.save();return buffer.getvalue()
