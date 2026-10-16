"""Hypothetical intensity split anchored to an explicit reference probability."""
from dataclasses import dataclass
import math
from numbers import Real
import numpy as np


@dataclass(frozen=True)
class PositiveGapMixture:
    sensitive_share: float
    gamma_per_pp: float
    lock_in: bool = True

    def __post_init__(self):
        for name in ('sensitive_share','gamma_per_pp'):
            value=getattr(self,name)
            if isinstance(value,bool) or not isinstance(value,Real):
                raise TypeError(name+' must be real')
            if not math.isfinite(value) or value<0:
                raise ValueError(name+' must be finite and nonnegative')
        if self.sensitive_share>1:raise ValueError('Share must be in [0,1]')
        if not isinstance(self.lock_in,bool):raise TypeError('lock_in must be boolean')

    def probability(self,reference_probability,gap_pp):
        """gap_pp is market minus existing engine coupon in percentage points.

        The caller supplies the reference probability; the kernel does not
        estimate it or add a hard floor after applying the intensity mixture.
        """
        p=np.asarray(reference_probability,dtype=float);g=np.asarray(gap_pp,dtype=float)
        if p.shape!=g.shape:raise ValueError('Reference and gaps must align')
        if np.any(~np.isfinite(p)) or np.any((p<0)|(p>=1)) or np.any(~np.isfinite(g)):
            raise ValueError('Need finite gaps and probabilities in [0,1)')
        if not self.lock_in or self.sensitive_share==0 or self.gamma_per_pp==0:return p.copy()
        positive=np.maximum(g,0.)
        factor=(1-self.sensitive_share)+self.sensitive_share*np.exp(-self.gamma_per_pp*positive)
        adjusted=-np.expm1(np.log1p(-p)*factor)
        return np.where(positive==0,p,adjusted)
