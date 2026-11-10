#!/usr/bin/env python3
"""Compute standard System Usability Scale (SUS) scores per participant.

Scoring (Brooke 1996): odd items contribute (score - 1), even items contribute
(5 - score); the sum is multiplied by 2.5 to give a 0-100 score.
Reads the clean combined workbook and writes sus_scores.csv / sus_scores.md.
"""
import sys, math
from pathlib import Path
import pandas as pd
import numpy as np

import sys
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("Experiment_combined_clean.xlsx")  # workbook path
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("outputs")
OUT.mkdir(parents=True, exist_ok=True)
ITEMS = [f"usab_sus_{i}" for i in range(1, 11)]

def main():
    df = pd.read_excel(SRC, sheet_name="Combined")
    sus = df[ITEMS].copy()
    complete = sus.notna().all(axis=1)
    contrib = pd.DataFrame(index=df.index)
    for i, col in enumerate(ITEMS, start=1):
        contrib[col] = (sus[col] - 1) if i % 2 == 1 else (5 - sus[col])
    df["sus_score"] = contrib.sum(axis=1, min_count=10) * 2.5
    out = df.loc[:, ["experiment_date", "crossover_user_id", "crossover_group"] + ITEMS + ["sus_score"]]
    out.to_csv(OUT / "sus_scores.csv", index=False)

    s = df.loc[complete, "sus_score"]
    n = len(s); mean = s.mean(); sd = s.std(ddof=1); se = sd / math.sqrt(n)
    from scipy import stats
    tcrit = stats.t.ppf(0.975, n - 1)
    ci = (mean - tcrit * se, mean + tcrit * se)
    med = s.median(); q1, q3 = s.quantile([0.25, 0.75])
    ge68 = int((s >= 68).sum()); lt50 = int((s < 50).sum())
    n_none = int(sus.isna().all(axis=1).sum()); n_partial = int((~complete).sum() - n_none)
    # Cronbach's alpha on the 10 scored contributions (complete cases)
    c = contrib.loc[complete]
    k = c.shape[1]; alpha = k / (k - 1) * (1 - c.var(ddof=1).sum() / c.sum(axis=1).var(ddof=1))
    # Sauro-Lewis curved grading scale (Sauro & Lewis 2016, Table 8.x)
    def grade(x):
        bands = [(84.1, "A+"), (80.8, "A"), (78.9, "A-"), (77.2, "B+"), (74.1, "B"), (72.6, "B-"),
                 (71.1, "C+"), (65.0, "C"), (62.7, "C-"), (51.7, "D")]
        for cut, g in bands:
            if x >= cut: return g
        return "F"
    item_means = sus.loc[complete].mean().round(2)
    lines = [
        "# SUS scores (standard 0-100 scoring)", "",
        f"Source: `{SRC}` sheet `Combined`; n = {n} participants with all 10 items "
        f"({n_none} of {len(df)} answered no SUS item and {n_partial} answered some but not all items; both excluded).", "",
        "| Statistic | Value |", "|---|---|",
        f"| n | {n} |", f"| Mean | {mean:.1f} |", f"| SD | {sd:.1f} |",
        f"| 95% CI (t) | {ci[0]:.1f} to {ci[1]:.1f} |", f"| Median (IQR) | {med:.1f} ({q1:.1f}-{q3:.1f}) |",
        f"| Range | {s.min():.1f} to {s.max():.1f} |",
        f"| Share >= 68 (mean of published SUS scores) | {ge68}/{n} ({100*ge68/n:.0f}%) |",
        f"| Share < 50 | {lt50}/{n} ({100*lt50/n:.0f}%) |",
        f"| Sauro-Lewis curved grade of the mean | {grade(mean)} |",
        f"| Nearest Bangor et al. (2009) adjective-group mean | {'good (71.4)' if abs(mean-71.4) < abs(mean-85.5) and abs(mean-71.4) < abs(mean-50.9) else 'see Bangor Table 3'} |",
        f"| Cronbach's alpha (10 items) | {alpha:.2f} |", "",
        "Per-item mean raw response (1-5, before reversal):", "",
        "| Item | Mean |", "|---|---|",
    ] + [f"| {c_} | {v} |" for c_, v in item_means.items()] + [
        "", "Individual scores (sorted): " + ", ".join(f"{v:g}" for v in sorted(s)), ""]
    (OUT / "sus_scores.md").write_text("\n".join(lines))
    print("\n".join(lines))

if __name__ == "__main__":
    main()
