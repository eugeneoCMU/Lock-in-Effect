from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hazard"))
from soma_fresh_sample import allocate_counts


def test_largest_remainder_allocation_is_exact_and_deterministic():
    target = {(0.02, "2020"): 0.333, (0.02, "2021"): 0.333,
              (0.025, "2021"): 0.334}
    counts = allocate_counts(target, 100)
    assert sum(counts.values()) == 100
    assert counts == {(0.02, "2020"): 33, (0.02, "2021"): 33,
                      (0.025, "2021"): 34}
