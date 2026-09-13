"""Small outward-rounded Decimal interval implementation (50 digits).

Extra adjacent representable values enclose correctly rounded arithmetic,
including sqrt/ln whose Decimal rounding is ROUND_HALF_EVEN.
"""
from decimal import Decimal, localcontext

D = lambda x: x if isinstance(x, Decimal) else Decimal(str(x))

class I:
    def __init__(self, lo, hi=None):
        self.lo, self.hi = D(lo), D(lo if hi is None else hi)
        if not self.lo.is_finite() or not self.hi.is_finite() or self.lo > self.hi:
            raise ValueError('Invalid finite interval')

    @staticmethod
    def rounded(fn):
        with localcontext() as c:
            c.prec = 50
            lo, hi = fn()
            return I(lo.next_minus(), hi.next_plus())

    def __add__(self, b):
        b = box(b)
        return I.rounded(lambda: (self.lo+b.lo, self.hi+b.hi))
    __radd__ = __add__
    def __neg__(self): return I(self.hi.copy_negate(), self.lo.copy_negate())
    def __sub__(self,b): return self + (-box(b))
    def __rsub__(self,b): return box(b) + (-self)
    def __mul__(self,b):
        b = box(b)
        def op():
            vals = [a*x for a in (self.lo,self.hi) for x in (b.lo,b.hi)]
            return min(vals),max(vals)
        return I.rounded(op)
    __rmul__=__mul__
    def __truediv__(self,b):
        b=box(b)
        if b.lo <= 0 <= b.hi: raise ValueError('Interval denominator includes zero')
        return self*I.rounded(lambda:(1/b.hi,1/b.lo))
    def square(self):
        def op():
            vals=[self.lo*self.lo,self.hi*self.hi]
            return (D(0) if self.lo<=0<=self.hi else min(vals)),max(vals)
        ans=I.rounded(op)
        return I(max(D(0),ans.lo),ans.hi)
    def sqrt(self):
        if self.lo < 0: raise ValueError('Negative squared speed')
        ans=I.rounded(lambda:(self.lo.sqrt(),self.hi.sqrt()))
        return I(max(D(0),ans.lo),ans.hi)
    def ln(self):
        if self.lo<=0: raise ValueError('Nonpositive logarithm')
        return I.rounded(lambda:(self.lo.ln(),self.hi.ln()))
    def floats(self):
        # Display only. These rounded float endpoints are not used for certificates.
        return [float(self.lo),float(self.hi)]
    def exact(self): return [str(self.lo),str(self.hi)]
    def contains(self,x): return self.lo<=D(x)<=self.hi

def box(x): return x if isinstance(x,I) else I(x)

def characteristics(s,g):
    a2=g*s['p']/s['rho']
    b2=sum(x.square() for x in s['B'])/s['rho']
    ca2=s['B'][0].square()/s['rho']
    total=a2+b2
    disc=total.square()-4*a2*ca2
    # The exact ideal-MHD discriminant is nonnegative. Intersect its enclosure.
    disc=I(max(D(0),disc.lo),max(D(0),disc.hi))
    cf2=(total+disc.sqrt())/2
    return {'fast':cf2.sqrt(),'alfven_n':ca2.sqrt(),'slow':(a2*ca2/cf2).sqrt()}
