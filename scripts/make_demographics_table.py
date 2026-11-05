#!/usr/bin/env python3
"""Build the participant-characteristics table (n = 30) from the clean workbook.

Writes demographics_table.csv and demographics_table.md. Denominators: the
demographic items came from the usability questionnaire (27 respondents); the
back-pain profile and session/arm fields are available for all 30.
"""
from pathlib import Path
import pandas as pd

import sys
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("Experiment_combined_clean.xlsx")  # workbook path
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("outputs")
OUT.mkdir(parents=True, exist_ok=True)

AGE = {"18_20": "18-20", "21_25": "21-25", "26_30": "26-30", "31_35": "31-35", "36_plus": "36 or older"}
GENDER = {"female": "Female", "male": "Male"}
LANG = {"arabic": "Arabic", "hebrew": "Hebrew", "russian": "Russian", "english": "English", "other": "Other"}
DUR = {"lt_1_month": "Less than 1 month", "1_3_months": "1-3 months", "3_6_months": "3-6 months",
       "6_12_months": "6-12 months", "1_5_years": "1-5 years", "gt_5_years": "More than 5 years"}
FREQ = {"less_than_half": "Less than half the days", "half_days": "Half the days or more", "daily": "Every day"}
SESSION = {"Jan4": "4 January 2026", "Jan22": "21-22 January 2026"}
ARM = {"Group1": "CA first, then form", "Group2": "Form first, then CA"}

def block(df, col, label, mapping, order=None, denom_note=None):
    s = df[col]
    answered = s.notna().sum()
    counts = s.value_counts()
    keys = order or list(mapping)
    rows = []
    for k in keys:
        n = int(counts.get(k, 0))
        if n == 0 and k not in counts: continue
        rows.append((label, mapping[k], n, answered, f"{n} ({100*n/answered:.0f}%)"))
    return rows

def main():
    df = pd.read_excel(SRC, sheet_name="Combined")
    rows = []
    rows += block(df, "usab_demographics_age_range", "Age range (years)", AGE)
    rows += block(df, "usab_demographics_gender", "Gender", GENDER)
    rows += block(df, "usab_demographics_language", "Main language spoken at home", LANG,
                  order=["arabic", "hebrew", "russian", "english", "other"])
    rows += block(df, "bp_q1_duration", "Duration of back pain reported in the form", DUR)
    rows += block(df, "bp_q2_frequency", "Frequency of back pain in the past 6 months (form)", FREQ)
    pain = df["bp_q3_average_pain"]
    rows.append(("Average pain in the past 7 days (0-10, form)", "Median (IQR)", None, int(pain.notna().sum()),
                 f"{pain.median():.0f} ({pain.quantile(0.25):.0f}-{pain.quantile(0.75):.0f})"))
    rows += block(df, "experiment_date", "Experiment session", SESSION)
    rows += block(df, "crossover_group", "Cross-over arm", ARM)
    rows += block(df, "exit_preference", "Exit preference", {"Chatbot": "CA", "Questionnaire": "Form", "No preference": "No preference"})
    tab = pd.DataFrame(rows, columns=["Characteristic", "Category", "n", "Answered", "n (%)"])
    tab.to_csv(OUT / "demographics_table.csv", index=False)
    md = ["# Table 1. Participant characteristics (N = 30)", "",
          "| Characteristic | Category | n (%) |", "|---|---|---|"]
    last = None
    for r in rows:
        lab = r[0] if r[0] != last else ""
        if r[0] != last:
            lab = f"{r[0]} (n = {r[3]})"
        md.append(f"| {lab} | {r[1]} | {r[4]} |"); last = r[0]
    md += ["", "Demographic items were part of the usability questionnaire, which 27 of the 30 participants completed; "
           "the back-pain profile comes from the 43-item form, which all 30 completed. Percentages use the number answering each item."]
    (OUT / "demographics_table.md").write_text("\n".join(md))
    print("\n".join(md))

if __name__ == "__main__":
    main()
