"""Matched positive-gap mixture with only a final hard floor added.

This is not the earlier signed-rate production hazard. The wrapped mixture
retains exactly the same share, response strength and intensity conversion.
"""
from dataclasses import dataclass
import math
from numbers import Real
import numpy as np
from hazard.positive_gap_mixture import PositiveGapMixture


@dataclass(frozen=True)
class FloorClampedMixture:
    mixture: PositiveGapMixture
    minimum_probability: float

    def __post_init__(self):
        if not isinstance(self.mixture,PositiveGapMixture):raise TypeError('Need a positive-gap mixture')
        p=self.minimum_probability
        if isinstance(p,bool) or not isinstance(p,Real):raise TypeError('Floor must be real')
        if not math.isfinite(p) or not 0<=p<1:raise ValueError('Floor must lie in [0,1)')

    def probability(self,reference_probability,gap_pp):
        result=self.mixture.probability(reference_probability,gap_pp)
        reference=np.asarray(reference_probability,dtype=float)
        if np.any(reference<self.minimum_probability):
            raise ValueError('Floor exceeds reference; comparison would change the baseline')
        return np.maximum(result,self.minimum_probability)
