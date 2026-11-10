#!/usr/bin/env python3
"""Active conversation duration per participant from Open WebUI chat exports.

Time-on-task for the conversational agent (CA) is computed from the chat logs rather
than from the cross-over platform's step timer, which was unreliable (see the paper,
Methods / "Time-on-task imputation").  For each participant, all user messages across
all of their chat sessions are pooled and sorted; the active duration is the elapsed
time from the first to the last user message minus every inter-message gap longer than
the idle threshold (180 s in the primary analysis; 120 s and 300 s in the sensitivity
analysis, Table 4).

Usage:
  python3 compute_chat_durations.py --workbook Experiment_combined_clean.xlsx \
      --export all-chats-export-<jan4>.json --export all-chats-export-<jan22>.json \
      --thresholds 120 180 300 --out outputs/chat_durations.csv

The workbook (sheet "Combined") provides the mapping crossover_user_id -> chatbot_uuid
(the Open WebUI user id).  Chat exports are the JSON files produced by Open WebUI's
"export all chats" (a list of chat objects with chat.history.messages or chat.messages,
each message carrying role and a Unix timestamp).  Chats are de-duplicated by chat id,
so overlapping exports can be passed together.
"""
import argparse
import json
from collections import defaultdict

import numpy as np
import pandas as pd


def load_user_messages(export_paths, exclude_chats=()):
    """Return {openwebui_user_id: sorted list of user-message timestamps (s)}."""
    seen = set()
    stamps = defaultdict(list)
    for path in export_paths:
        with open(path) as fh:
            chats = json.load(fh)
        for chat in chats:
            if chat["id"] in seen or any(chat["id"].startswith(x) for x in exclude_chats):
                continue
            seen.add(chat["id"])
            body = chat.get("chat", {})
            msgs = body.get("messages") or list(body.get("history", {}).get("messages", {}).values())
            for m in msgs:
                if m.get("role") == "user" and m.get("timestamp"):
                    stamps[chat["user_id"]].append(float(m["timestamp"]))
    return {u: sorted(v) for u, v in stamps.items()}


def active_duration(ts, threshold):
    """Elapsed first->last user message minus gaps > threshold; also gap statistics."""
    if len(ts) < 2:
        return dict(span_min=0.0, active_min=0.0, n_msgs=len(ts), n_gaps=0, n_idle_gaps=0, idle_min=0.0)
    gaps = np.diff(ts)
    idle = gaps[gaps > threshold]
    span = ts[-1] - ts[0]
    return dict(span_min=span / 60, active_min=(span - idle.sum()) / 60, n_msgs=len(ts),
                n_gaps=len(gaps), n_idle_gaps=int(len(idle)), idle_min=idle.sum() / 60)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workbook", required=True)
    ap.add_argument("--sheet", default="Combined")
    ap.add_argument("--export", action="append", required=True, help="Open WebUI chat export JSON (repeatable)")
    ap.add_argument("--thresholds", nargs="+", type=int, default=[120, 180, 300])
    ap.add_argument("--out", default="chat_durations.csv")
    ap.add_argument("--exclude-chats", nargs="*", default=[],
                    help="chat ids (or id prefixes) to ignore, e.g. a session aborted by the token-limit "
                         "crash and restarted from scratch; the published analysis excluded chat 5db880bb")
    args = ap.parse_args()

    df = pd.read_excel(args.workbook, sheet_name=args.sheet)
    stamps = load_user_messages(args.export, args.exclude_chats)
    rows = []
    all_gaps = []
    for _, r in df.iterrows():
        ts = stamps.get(r["chatbot_uuid"], [])
        if len(ts) > 1:
            all_gaps.extend(np.diff(ts))
        row = dict(experiment_date=r["experiment_date"], crossover_user_id=r["crossover_user_id"],
                   crossover_group=r["crossover_group"], n_user_msgs=len(ts))
        for t in args.thresholds:
            d = active_duration(ts, t)
            row[f"active_min_{t}s"] = round(d["active_min"], 2)
            row[f"idle_gaps_{t}s"] = d["n_idle_gaps"]
        row["span_min"] = round(active_duration(ts, 10**9)["span_min"], 2)
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(args.out, index=False)
    all_gaps = np.asarray(all_gaps)
    print(f"{len(out)} participants, {len(all_gaps)} inter-message gaps "
          f"(75th pct {np.percentile(all_gaps, 75):.0f} s, 90th pct {np.percentile(all_gaps, 90):.0f} s)")
    for t in args.thresholds:
        col = out[f"active_min_{t}s"]
        print(f"threshold {t:>3d} s: gaps classified active {np.mean(all_gaps <= t) * 100:.0f}%, "
              f"CA median {col.median():.1f} min (IQR {col.quantile(.25):.1f}-{col.quantile(.75):.1f})")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
