#!/usr/bin/env python3
"""Reproduce the quantitative outcomes of the back-pain CA cross-over study from the
cleaned participant workbook (sheet "Combined", one row per participant, N = 30).

Usage:
  python3 analyze_outcomes.py Experiment_combined_clean.xlsx [--durations outputs/chat_durations.csv]
      [--metrics outputs/conversation_metrics.csv] [--out outputs/analysis_report.md]

Sections: usability / usefulness / conversation-quality ratings (Table 2), SUS composite,
intention to use, exit preference and exploratory subgroup tests, completion time
(Wilcoxon, Table 4 sensitivity analysis when --durations is given), conversation
characteristics, and completeness / correctness / efficiency when --metrics is given.
"""
import argparse
import io
import sys
from contextlib import redirect_stdout

import numpy as np
import pandas as pd
from scipy import stats

SUS = [f"usab_sus_{i}" for i in range(1, 11)]
PU = [f"usab_pu_{i}" for i in range(1, 7)]
PEU = [f"usab_peu_{i}" for i in range(1, 7)]
FCQ = [f"usab_fcq_{i}" for i in range(1, 11)]          # 8 Grice-maxim items + 2 conversational-flow items
INTENT_YN = ["usab_intent_recommend_friend", "usab_intent_use_again", "usab_intent_use_routinely", "usab_intent_pay"]
INTENT_SCALE = "usab_intent_recommend_scale"           # 1-5


def cronbach_alpha(items):
    items = items.dropna()
    k = items.shape[1]
    return k / (k - 1) * (1 - items.var(ddof=1).sum() / items.sum(axis=1).var(ddof=1))


def median_of_medians(df, cols, label, scale):
    d = df[cols].dropna()
    per_user = d.median(axis=1)
    q1, q3 = per_user.quantile([.25, .75])
    print(f"- {label}: median of per-user medians {per_user.median():g} (IQR {q1:g}-{q3:g}), "
          f"scale 1-{scale}, Cronbach's alpha {cronbach_alpha(d):.2f}, n = {len(d)}")
    return per_user


def sus_scores(df):
    d = df[SUS].dropna()
    odd = d[[f"usab_sus_{i}" for i in (1, 3, 5, 7, 9)]].sub(1).sum(axis=1)
    even = (5 - d[[f"usab_sus_{i}" for i in (2, 4, 6, 8, 10)]]).sum(axis=1)
    return (odd + even) * 2.5, d


def ci_mean(x):
    x = np.asarray(x, float)
    se = x.std(ddof=1) / np.sqrt(len(x))
    h = stats.t.ppf(.975, len(x) - 1) * se
    return x.mean() - h, x.mean() + h


def boot_ci_median(x, n=10000, seed=0):
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float)
    meds = np.median(rng.choice(x, (n, len(x)), replace=True), axis=1)
    return np.percentile(meds, [2.5, 97.5])


def wilcoxon_report(a, b, label):
    a, b = np.asarray(a, float), np.asarray(b, float)
    n = len(a)
    res = stats.wilcoxon(a, b, zero_method="wilcox")
    d = a - b
    nz = d[d != 0]
    n_eff = len(nz)
    mu = n_eff * (n_eff + 1) / 4
    sigma = np.sqrt(n_eff * (n_eff + 1) * (2 * n_eff + 1) / 24)
    w_plus = np.sum(stats.rankdata(np.abs(nz))[nz > 0])
    w_minus = np.sum(stats.rankdata(np.abs(nz))[nz < 0])
    z = (min(w_plus, w_minus) - mu) / sigma
    r = abs(z) / np.sqrt(n)
    print(f"- {label}: CA median {np.median(a):.1f} min (IQR {np.percentile(a, 25):.1f}-{np.percentile(a, 75):.1f}) "
          f"vs form {np.median(b):.1f} min (IQR {np.percentile(b, 25):.1f}-{np.percentile(b, 75):.1f}); "
          f"W = {min(w_plus, w_minus):.1f}, Z = {z:.2f}, p = {res.pvalue:.3f}, r = {r:.2f}; "
          f"{int((d > 0).sum())}/{n} longer with the CA, {int((d == 0).sum())} tied; median difference {np.median(d):.1f} min")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workbook")
    ap.add_argument("--sheet", default="Combined")
    ap.add_argument("--durations", help="chat_durations.csv from compute_chat_durations.py (adds the Table 4 sensitivity analysis)")
    ap.add_argument("--metrics", help="per-participant completeness/correctness/efficiency CSV")
    ap.add_argument("--out", help="write the report to this Markdown file as well as stdout")
    args = ap.parse_args()

    buf = io.StringIO()
    with redirect_stdout(buf):
        run(args)
    sys.stdout.write(buf.getvalue())
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(buf.getvalue())


def run(args):
    df = pd.read_excel(args.workbook, sheet_name=args.sheet)
    print(f"# Analysis report\n\nWorkbook: {args.workbook} (sheet {args.sheet}), N = {len(df)} participants "
          f"({(df.experiment_date == 'Jan4').sum()} on 4 Jan, {(df.experiment_date != 'Jan4').sum()} on 21-22 Jan); "
          f"{df.crossover_group.value_counts().to_dict()}\n")

    # ---- Table 2: ratings
    print("## Usability, usefulness and conversation quality (Table 2)\n")
    median_of_medians(df, PU, "TAM perceived usefulness (6 items)", 7)
    median_of_medians(df, PEU, "TAM perceived ease of use (6 items)", 7)
    median_of_medians(df, FCQ, "Conversation quality: Grice's maxims + flow (10 items)", 5)
    scores, d = sus_scores(df)
    d = d.copy()
    for i in (2, 4, 6, 8, 10):                           # reverse negatively worded items before alpha
        d[f"usab_sus_{i}"] = 6 - d[f"usab_sus_{i}"]
    lo, hi = ci_mean(scores)
    print(f"- SUS (standard 0-100 scoring, n = {len(scores)}): mean {scores.mean():.1f} (SD {scores.std(ddof=1):.1f}; "
          f"95% CI {lo:.1f}-{hi:.1f}); median {scores.median():.1f} (IQR {scores.quantile(.25):.1f}-{scores.quantile(.75):.1f}); "
          f"range {scores.min():g}-{scores.max():g}; {(scores >= 68).sum()}/{len(scores)} >= 68; {(scores < 50).sum()} < 50; "
          f"Cronbach's alpha {cronbach_alpha(d):.2f}")

    # ---- intention to use
    print("\n## Intention to use\n")
    it = df[INTENT_YN + [INTENT_SCALE]].dropna()
    comp = pd.concat([(it[INTENT_YN] == "yes").astype(float), (it[INTENT_SCALE] - 1) / 4], axis=1).mean(axis=1)
    bci = boot_ci_median(comp)
    print(f"- composite (4 yes/no items coded 0/1 + recommend scale rescaled to 0-1, averaged), n = {len(comp)}: "
          f"median {comp.median():.2f} (IQR {comp.quantile(.25):.2f}-{comp.quantile(.75):.2f}; bootstrap 95% CI of the median "
          f"{bci[0]:.2f}-{bci[1]:.2f}); Cronbach's alpha {cronbach_alpha(pd.concat([(it[INTENT_YN] == 'yes').astype(float), (it[INTENT_SCALE] - 1) / 4], axis=1)):.2f}")
    for c in INTENT_YN:
        print(f"- {c}: yes {(df[c] == 'yes').sum()}/{df[c].notna().sum()} ({(df[c] == 'yes').mean() / df[c].notna().mean() * 100:.0f}%)")

    # ---- exit preference
    print("\n## Exit preference\n")
    ep = df.exit_preference.dropna()
    counts = ep.value_counts()
    ca, form, none = counts.get("Chatbot", 0), counts.get("Questionnaire", 0), counts.get("No preference", 0)
    n = len(ep)
    chi = stats.chisquare([ca, form, none])
    print(f"- n = {n}: CA {ca} ({ca / n * 100:.1f}%), form {form} ({form / n * 100:.1f}%), no preference {none} ({none / n * 100:.1f}%)")
    print(f"- chi-square goodness of fit vs uniform: chi2 = {chi.statistic:.2f}, df = 2, p = {chi.pvalue:.3f}")
    print(f"- binomial test, CA vs 1/3 (one-sided): p = {stats.binomtest(ca, n, 1 / 3, alternative='greater').pvalue:.3f}")
    print(f"- binomial test, CA vs form among those with a preference (two-sided): p = {stats.binomtest(ca, ca + form, .5).pvalue:.3f}")

    print("\n### Exploratory subgroup analyses (sparse cells; hypothesis-generating only)\n")
    sub = df[df.exit_preference.notna()].copy()
    lang = sub.usab_demographics_language.fillna("other").astype(str).str.lower()
    sub["lang3"] = np.select([lang.str.startswith("arab"), lang.str.startswith("heb")], ["Arabic", "Hebrew"], "Other")
    for var, label in [("lang3", "home language (Arabic / Hebrew / other)"), ("crossover_group", "cross-over order")]:
        ct = pd.crosstab(sub[var], sub.exit_preference)
        chi2, p, dof, exp = stats.chi2_contingency(ct)
        print(f"- {label} x preference: chi2 = {chi2:.2f}, df = {dof}, p = {p:.3f}; "
              f"{(exp < 5).mean() * 100:.0f}% of expected cells < 5; Bonferroni-adjusted (x2) p = {min(1, p * 2):.3f}")
        print("  " + ct.to_string().replace("\n", "\n  "))
    ct2 = pd.crosstab(sub.crossover_group, sub.exit_preference == "Chatbot")
    print(f"- cross-over order x (CA vs other), Fisher exact p = {stats.fisher_exact(ct2)[1]:.3f}")

    # ---- completion time
    print("\n## Completion time (Hypothesis 4)\n")
    for c in ["step_C_started", "step_C_ended"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    form_min = (df.step_C_ended - df.step_C_started).dt.total_seconds() / 60
    ca_min = df.chatlog_active_duration_min
    print("Form time from the platform's step log; CA time from chat logs with idle gaps > 180 s removed (workbook column).\n")
    wilcoxon_report(ca_min, form_min, "primary (180 s threshold)")
    j22 = df.experiment_date != "Jan4"
    print(f"- 21-22 Jan subsample (n = {j22.sum()}, unaffected by the token-limit error): CA median {ca_min[j22].median():.1f} min")
    if args.durations:
        dur = pd.read_csv(args.durations).merge(df[["experiment_date", "crossover_user_id"]], on=["experiment_date", "crossover_user_id"])
        dur = dur.set_index(["experiment_date", "crossover_user_id"]).loc[list(zip(df.experiment_date, df.crossover_user_id))]
        print("\n### Sensitivity analysis across idle-gap thresholds (Table 4)\n")
        for t in (120, 180, 300):
            col = f"active_min_{t}s"
            if col in dur:
                wilcoxon_report(dur[col].values, form_min.values, f"{t} s threshold")
                print(f"  21-22 Jan subsample CA median at {t} s: {dur[col].values[j22.values].mean() and np.median(dur[col].values[j22.values]):.1f} min")

    # ---- conversation characteristics
    print("\n## Conversation characteristics\n")
    print(f"- words per conversation: mean {df.conversation_word_count.mean():.0f} (SD {df.conversation_word_count.std(ddof=1):.0f}; "
          f"median {df.conversation_word_count.median():.0f}; range {df.conversation_word_count.min():.0f}-{df.conversation_word_count.max():.0f})")
    print(f"- user messages per participant: mean {df.chatlog_num_user_msgs.mean():.1f} (range {df.chatlog_num_user_msgs.min()}-{df.chatlog_num_user_msgs.max()})")
    print(f"- participants with more than one chat session: {(df.conversation_count > 1).sum()}")

    # ---- data quality metrics
    if args.metrics:
        m = pd.read_csv(args.metrics)
        print(f"\n## Completeness, correctness and efficiency (Table 3), n = {len(m)}\n")
        for col, label in [("pct_complete", "completeness (%)"), ("pct_correct", "correctness (%)"), ("efficiency", "efficiency (correct items per CA utterance)")]:
            x = m[col].dropna()
            lo, hi = ci_mean(x)
            print(f"- {label}: mean {x.mean():.2f} (SD {x.std(ddof=1):.2f}; 95% CI {lo:.2f}-{hi:.2f})")


if __name__ == "__main__":
    main()
