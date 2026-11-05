# Selection of the analysed participants

The cross-over platform recorded 115 user accounts across the two experiment sessions (4 January and 21–22 January 2026). The 30 participants analysed in the paper were selected as follows (counts are cumulative exclusions; usernames are not reproduced here).

| Step | Rule | Excluded | Remaining |
|---|---|---|---|
| 1 | Researcher / test accounts (identified by username) | 9 | 106 |
| 2 | No recorded chat with the CA (no conversation file could be matched to the account) | 45 | 61 |
| 3 | Chat present but none of the three questionnaires (back-pain form, usability, exit) submitted | 8 | 53 |
| 4 | Manual exclusion after review of the 21–22 January data (two accounts belonging to the research team) | 2 | 51 |
| 5a | Minimal chats: fewer than 200 words in total (one or two user messages, no substantive interaction) | 15 | 36 |
| 5b | Short chats: 200–800 words, reviewed individually and judged not to be a genuine attempt at the interview | 4 | 32 |
| 6 | Questionnaire (form) completion time implausible, judged idle during the form step (reviewed individually) | 2 | 30 |

A complete back-pain interview with the CA had a median length of roughly 1,650 words over 15–20 conversational turns, which motivated the thresholds in step 5.

Of the 30 analysed participants, 25 took part on 4 January and 5 on 21–22 January; 19 used the CA first (Group 1) and 11 used the form first (Group 2). Three participants (all Group 2) left the platform after the CA step and therefore have no usability or exit questionnaire; 27 completed all parts.

## Time-on-task

The platform's own step timer was unreliable for the CA step because a token-limit error on 4 January crashed sessions and reset the timer. CA time was therefore recomputed from the chat logs (`scripts/compute_chat_durations.py`): elapsed time from the first to the last user message, minus idle gaps longer than 180 s between consecutive user messages. The 120 s and 300 s thresholds are reported as a sensitivity analysis. Form time comes from the platform's step timer, which showed no anomalies for that step.
