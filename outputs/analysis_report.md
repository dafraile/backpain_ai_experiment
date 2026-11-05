# Analysis report

Workbook: /Users/david/backpain/backpain final analysis claude/Experiment_combined_clean.xlsx (sheet Combined), N = 30 participants (25 on 4 Jan, 5 on 21-22 Jan); {'Group1': 19, 'Group2': 11}

## Usability, usefulness and conversation quality (Table 2)

- TAM perceived usefulness (6 items): median of per-user medians 6 (IQR 5-6), scale 1-7, Cronbach's alpha 0.98, n = 27
- TAM perceived ease of use (6 items): median of per-user medians 6 (IQR 5-7), scale 1-7, Cronbach's alpha 0.96, n = 27
- Conversation quality: Grice's maxims + flow (10 items): median of per-user medians 5 (IQR 4-5), scale 1-5, Cronbach's alpha 0.96, n = 27
- SUS (standard 0-100 scoring, n = 27): mean 71.8 (SD 18.2; 95% CI 64.5-79.0); median 75.0 (IQR 62.5-83.8); range 20-97.5; 16/27 >= 68; 2 < 50; Cronbach's alpha 0.83

## Intention to use

- composite (4 yes/no items coded 0/1 + recommend scale rescaled to 0-1, averaged), n = 27: median 0.75 (IQR 0.32-0.80; bootstrap 95% CI of the median 0.50-0.80); Cronbach's alpha 0.85
- usab_intent_recommend_friend: yes 21/27 (78%)
- usab_intent_use_again: yes 20/27 (74%)
- usab_intent_use_routinely: yes 17/27 (63%)
- usab_intent_pay: yes 6/27 (22%)

## Exit preference

- n = 27: CA 15 (55.6%), form 8 (29.6%), no preference 4 (14.8%)
- chi-square goodness of fit vs uniform: chi2 = 6.89, df = 2, p = 0.032
- binomial test, CA vs 1/3 (one-sided): p = 0.014
- binomial test, CA vs form among those with a preference (two-sided): p = 0.210

### Exploratory subgroup analyses (sparse cells; hypothesis-generating only)

- home language (Arabic / Hebrew / other) x preference: chi2 = 10.32, df = 4, p = 0.035; 89% of expected cells < 5; Bonferroni-adjusted (x2) p = 0.071
  exit_preference  Chatbot  No preference  Questionnaire
  lang3                                                 
  Arabic                11              2              1
  Hebrew                 3              0              3
  Other                  1              2              4
- cross-over order x preference: chi2 = 6.10, df = 2, p = 0.047; 67% of expected cells < 5; Bonferroni-adjusted (x2) p = 0.095
  exit_preference  Chatbot  No preference  Questionnaire
  crossover_group                                       
  Group1                13              1              5
  Group2                 2              3              3
- cross-over order x (CA vs other), Fisher exact p = 0.087

## Completion time (Hypothesis 4)

Form time from the platform's step log; CA time from chat logs with idle gaps > 180 s removed (workbook column).

- primary (180 s threshold): CA median 13.6 min (IQR 10.7-18.1) vs form 6.4 min (IQR 4.6-8.9); W = 80.0, Z = -3.14, p = 0.001, r = 0.57; 24/30 longer with the CA, 0 tied; median difference 5.8 min
- 21-22 Jan subsample (n = 5, unaffected by the token-limit error): CA median 12.4 min

### Sensitivity analysis across idle-gap thresholds (Table 4)

- 120 s threshold: CA median 9.3 min (IQR 8.1-11.2) vs form 6.4 min (IQR 4.6-8.9); W = 146.0, Z = -1.78, p = 0.077, r = 0.32; 19/30 longer with the CA, 0 tied; median difference 2.0 min
  21-22 Jan subsample CA median at 120 s: 8.8 min
- 180 s threshold: CA median 13.6 min (IQR 10.7-18.1) vs form 6.4 min (IQR 4.6-8.9); W = 80.0, Z = -3.14, p = 0.001, r = 0.57; 24/30 longer with the CA, 0 tied; median difference 5.8 min
  21-22 Jan subsample CA median at 180 s: 12.4 min
- 300 s threshold: CA median 18.0 min (IQR 12.5-24.8) vs form 6.4 min (IQR 4.6-8.9); W = 44.0, Z = -3.88, p = 0.000, r = 0.71; 26/30 longer with the CA, 0 tied; median difference 8.7 min
  21-22 Jan subsample CA median at 300 s: 13.0 min

## Conversation characteristics

- words per conversation: mean 1947 (SD 468; median 1972; range 863-2974)
- user messages per participant: mean 17.5 (range 9-26)
- participants with more than one chat session: 2

## Completeness, correctness and efficiency (Table 3), n = 30

- completeness (%): mean 100.00 (SD 0.00; 95% CI 100.00-100.00)
- correctness (%): mean 98.31 (SD 2.85; 95% CI 97.25-99.38)
- efficiency (correct items per CA utterance): mean 2.37 (SD 0.52; 95% CI 2.18-2.56)
