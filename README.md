# Back-pain conversational agent: cross-over evaluation pipeline

Processing and analysis code for

> Fraile Navarro D, Peleg M. *Evaluating a Large Language Model Conversational Agent for Collecting Standardized Back Pain Data: A Cross-Over Study of Accuracy, Usability, and User Preference.* Methods of Information in Medicine (under review, 2026).

and the companion development report

> Fraile Navarro D, Peleg M. Conversational AI for automated patient questionnaire completion: development insights and design principles. arXiv:2602.19507 (2026). https://doi.org/10.48550/arXiv.2602.19507

The study compared a GPT-based conversational agent (CA) that collects the 43-item NIH Task Force minimal dataset for chronic low back pain with a standard web form, in a cross-over design with 30 university students (University of Haifa, January 2026; ethics approval 472/25).

## What is here

| Path | Purpose |
|---|---|
| `scripts/match_conversations.py` | Links each Open WebUI chat export to a cross-over platform participant (chat user id → Open WebUI user → e-mail → platform credential → participant id and arm). |
| `scripts/process_chats.py` | Turns an Open WebUI chat export into one readable transcript per chat and one pre-filled completeness/correctness grading template per chat (word and utterance counts, coded answers), used for the manual grading. |
| `scripts/compute_chat_durations.py` | Active CA time-on-task from the chat logs: first to last user message, minus inter-message gaps longer than an idle threshold (180 s primary; 120 s and 300 s sensitivity analysis, Table 4). |
| `scripts/compute_sus.py` | System Usability Scale composite (Brooke's 0–100 scoring) per participant, summary statistics, Cronbach's α. |
| `scripts/make_demographics_table.py` | Participant characteristics table (Table 1). |
| `scripts/analyze_outcomes.py` | All quantitative outcomes: TAM / Grice ratings, SUS, intention to use, exit preference and exploratory subgroup tests, completion time (Wilcoxon), conversation characteristics, completeness / correctness / efficiency. Writes `outputs/analysis_report.md`. |
| `docs/data_cleaning.md` | How the 30 analysed participants were selected from the raw platform records (counts and thresholds). |

## Running

```bash
pip install -r requirements.txt
W=Experiment_combined_clean.xlsx          # cleaned workbook, sheet "Combined", one row per participant (not distributed)
python3 scripts/compute_chat_durations.py --workbook $W --export all-chats-export-jan4.json \
    --export all-chats-export-jan22.json --exclude-chats 5db880bb --out outputs/chat_durations.csv
python3 scripts/compute_sus.py $W outputs
python3 scripts/make_demographics_table.py $W outputs
python3 scripts/analyze_outcomes.py $W --durations outputs/chat_durations.csv \
    --metrics outputs/conversation_metrics.csv --out outputs/analysis_report.md
```

`--exclude-chats 5db880bb` drops one five-message chat that was aborted by the token-limit error of the 4 January session and restarted from scratch by the same participant; the published time-on-task uses the restarted session only.

Completeness, correctness and efficiency were graded manually by the two authors against the conversation transcripts; `analyze_outcomes.py --metrics` summarises a per-participant CSV of those grades (columns `pct_complete`, `pct_correct`, `efficiency`).

## Data

This repository distributes the processing and analysis scripts only. No study data are included, raw or derived: the chat logs, the cross-over platform database (`crossover.db`) and the Open WebUI database contain free-text health information from participants, and participant-level tables are not shared either. The scripts write their outputs to a local `outputs/` folder, which is git-ignored. Aggregate results are reported in the paper; the cleaned participant workbook is available from the authors on reasonable request, subject to the ethics approval.

## Reproduction notes

Run on the final workbook (5 November 2026), the scripts reproduce the published figures: SUS mean 71.8 (SD 18.2, 95% CI 64.5–79.0, n = 27, α = 0.83); exit preference 15 / 8 / 4 (χ² = 6.89, p = .032; binomial p = .014); subgroup tests (language χ² = 10.32, p = .035; order χ² = 6.10, p = .047, Fisher p = .087); completion time median 13.6 vs 6.4 min (Z = −3.14, p = .001, r = .57; 24/30 longer with the CA, median difference 5.8 min); Table 4 medians 9.3 / 13.6 / 18.0 min with 75% / 87% / 94% of the 496 inter-message gaps classified as active. Interquartile ranges can differ by up to one scale point from the manuscript depending on the quantile interpolation used. The manuscript reports `scipy`'s exact Wilcoxon p-values (p = .077 at the 120 s threshold).

## Licence

MIT (see `LICENSE`).
