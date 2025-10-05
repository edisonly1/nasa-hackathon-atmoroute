##unused

import numpy as np
# services/stats.py
from typing import List, Tuple

def poe_and_hist(samples: List[float], bins: List[float], threshold: float) -> Tuple[float, dict]:
    """
    Returns:
      poe: probability of exceedance P(X >= threshold) in [0,1]
      hist: {"bins": [...], "pdf": [...]} where pdf sums to 1 over the intervals
            [bins[i], bins[i+1]) for i < len(bins)-1, and [bins[-2], bins[-1]] for the last.
    """
    n = max(1, len(samples))

    #PoE (tail probability)
    tail = sum(1 for x in samples if x >= threshold) / n

    #Histogram (normalized)
    # Initialize counts for each interval between edges
    k = max(1, len(bins) - 1)
    counts = [0] * k
    b = bins

    for x in samples:
        # place x into the correct bin: [b[i], b[i+1]) except include rightmost in last bin
        idx = None
        for i in range(k - 1):
            if b[i] <= x < b[i + 1]:
                idx = i
                break
        if idx is None:
            # last bin gets everything >= b[-2] and <= b[-1]
            if x >= b[-2] and x <= b[-1]:
                idx = k - 1
        if idx is not None:
            counts[idx] += 1

    total = sum(counts)
    pdf = [c / total if total > 0 else 0.0 for c in counts]

    return tail, {"bins": bins, "pdf": pdf}
