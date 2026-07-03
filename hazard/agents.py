"""
MortgageAgent and vectorized MicrosimPool for literature microsim.

Burnout is cohort-level: cohort_burnout[stratum_id] broadcast to agents.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import polars as pl

from config import MARKOV_STATES, TERM_MONTHS


STATE_TO_CODE = {s: i for i, s in enumerate(MARKOV_STATES)}
CODE_TO_STATE = {i: s for s, i in STATE_TO_CODE.items()}

ABSORBING_STATES = {"Prepaid", "Defaulted", "Liquidated"}

STATE_TO_REGION = {}
_NORTHEAST = {"CT", "ME", "MA", "NH", "RI", "VT", "NJ", "NY", "PA"}
_MIDWEST = {"IL", "IN", "MI", "OH", "WI", "IA", "KS", "MN", "MO", "NE", "ND", "SD"}
_SOUTH = {"DE", "FL", "GA", "MD", "NC", "SC", "VA", "DC", "WV", "AL", "KY", "MS",
          "TN", "AR", "LA", "OK", "TX"}
_WEST = {"AZ", "CO", "ID", "MT", "NV", "NM", "UT", "WY", "AK", "CA", "HI", "OR", "WA"}
for s in _NORTHEAST:
    STATE_TO_REGION[s] = 0
for s in _MIDWEST:
    STATE_TO_REGION[s] = 1
for s in _SOUTH:
    STATE_TO_REGION[s] = 2
for s in _WEST:
    STATE_TO_REGION[s] = 3


@dataclass
class MortgageAgent:
    """Row-view of a single loan agent backed by MicrosimPool arrays."""

    pool: "MicrosimPool"
    idx: int

    @property
    def fico(self) -> int:
        return int(self.pool.fico[self.idx])

    @property
    def property_state(self) -> str:
        return self.pool.property_states[self.idx]

    @property
    def orig_ltv(self) -> float:
        return float(self.pool.orig_ltv[self.idx])

    @property
    def stratum_id(self) -> str:
        return self.pool.stratum_ids[self.idx]

    @property
    def loan_age(self) -> int:
        return int(self.pool.loan_age[self.idx])

    @property
    def balance(self) -> float:
        return float(self.pool.balance[self.idx])

    @property
    def coupon(self) -> float:
        return float(self.pool.coupon[self.idx])

    @property
    def orig_upb(self) -> float:
        return float(self.pool.orig_upb[self.idx])

    @property
    def burnout(self) -> float:
        return float(self.pool.burnout[self.idx])

    @property
    def state(self) -> str:
        return CODE_TO_STATE[int(self.pool.state_code[self.idx])]

    @property
    def active(self) -> bool:
        return bool(self.pool.active_mask[self.idx])


class MicrosimPool:
    """Vectorized loan pool with cohort-level burnout broadcast."""

    def __init__(
        self,
        loan_df: pl.DataFrame,
        regime: str = "US",
        rng: Optional[np.random.Generator] = None,
    ):
        self.regime = regime
        self.rng = rng or np.random.default_rng()
        self.n = len(loan_df)
        pdf = loan_df.to_pandas()

        self.loan_ids = pdf["loan_id"].values
        stratum_list = pdf["stratum_id"].astype(str).tolist()
        self.stratum_ids = stratum_list
        unique_strata = sorted(set(stratum_list))
        self._stratum_to_code = {s: i for i, s in enumerate(unique_strata)}
        self.stratum_id_code = np.array(
            [self._stratum_to_code[s] for s in stratum_list], dtype=np.int32
        )
        self.n_strata = len(unique_strata)

        self.fico = pdf["fico"].fillna(700).values.astype(np.float64)
        self.property_states = pdf["property_state"].fillna("CA").astype(str).values
        self.orig_ltv = pdf["orig_ltv"].fillna(80).values.astype(np.float64)
        self.coupon = pdf["coupon"].values.astype(np.float64)
        self.orig_upb = pdf["orig_upb"].values.astype(np.float64)
        self.balance = pdf["balance"].values.astype(np.float64)
        self.loan_age = pdf["loan_age"].fillna(36).values.astype(np.int32)

        states = pdf["state"].fillna("Current").astype(str).values
        self.state_code = np.array(
            [STATE_TO_CODE.get(s, 0) for s in states], dtype=np.int32
        )

        self.fico_z = (self.fico - self.fico.mean()) / max(self.fico.std(), 1.0)
        self.ltv_z = (self.orig_ltv - self.orig_ltv.mean()) / max(self.orig_ltv.std(), 1.0)
        self.region_code = np.array(
            [STATE_TO_REGION.get(str(s).strip(), 3) for s in self.property_states],
            dtype=np.int32,
        )

        self.stratum_orig_upb = np.zeros(self.n_strata, dtype=np.float64)
        for i in range(self.n):
            self.stratum_orig_upb[self.stratum_id_code[i]] += self.orig_upb[i]

        self.cohort_burnout = np.zeros(self.n_strata, dtype=np.float64)
        self.burnout = np.zeros(self.n, dtype=np.float64)
        self.rate_gap = np.zeros(self.n, dtype=np.float64)
        self.active_mask = np.ones(self.n, dtype=bool)
        self._update_active_mask()

        self.term_months = TERM_MONTHS

    def _update_active_mask(self):
        absorbing = np.isin(
            self.state_code,
            [STATE_TO_CODE[s] for s in ABSORBING_STATES],
        )
        self.active_mask = (~absorbing) & (self.balance > 0)

    def broadcast_burnout(self):
        """Broadcast cohort_burnout[stratum] to per-agent burnout array."""
        self.burnout = self.cohort_burnout[self.stratum_id_code]

    def agent(self, idx: int) -> MortgageAgent:
        return MortgageAgent(self, idx)

    def scale_to_holdings(self, target_billions: float):
        """Scale all balances so total UPB matches Fed holdings at QT start."""
        total = self.balance.sum()
        if total <= 0:
            return
        scale = (target_billions * 1e9) / total
        self.balance *= scale
        self.orig_upb *= scale
        self.stratum_orig_upb *= scale

    def total_exposure(self) -> float:
        return float(self.balance[self.active_mask].sum())
