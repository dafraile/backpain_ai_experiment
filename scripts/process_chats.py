#!/usr/bin/env python3
"""
Generate readable chat transcripts and populate evaluation templates per user.

Inputs:
  - all-chats-export-*.json: chatbot dialogue export.
  - Completness and Correctness EvaluationTemplateCSV.csv: template in CSV form.

Outputs:
  1. One text transcript per chat under output/conversations/.
  2. One populated template per chat (CSV) under output/workbooks/.
     Column D contains human-readable answers (Ai-Option text) wherever possible.
"""

from __future__ import annotations

import csv
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parent
CHAT_EXPORT = ROOT / "all-chats-export-1768523038898.json"
TEMPLATE_PATH = ROOT / "Completness and Correctness EvaluationTemplateCSV.csv"
OUTPUT_DIR = ROOT / "output"
CONVERSATIONS_DIR = OUTPUT_DIR / "conversations"
WORKBOOKS_DIR = OUTPUT_DIR / "workbooks"

QUESTION_COL = 2  # column C
ANSWER_COL = 3    # column D
OPTION_START_COL = 11  # column L

METRIC_ROWS = [
    (3, "#words by the user", "user_words"),
    (4, "#words by the bot", "bot_words"),
    (5, "#utterances by the user", "user_utterances"),
    (6, "#utterances by the bot", "bot_utterances"),
]

TEMPLATE_CELL_CLEARS = [
    (53, 1),  # B54
    (54, 1),  # B55
]

NUMERIC_QUESTIONS = {"Q3", "Q33", "Q40", "Q41"}

ANSWER_TOKEN_RE = re.compile(r"(Q\d+[a-d]?):([^;]+)")
QUESTION_ID_RE = re.compile(r"^(\d+)([a-d]?)")

MANUAL_OPTION_OVERRIDES: Dict[str, Dict[str, str]] = {
    "Q28": {
        "A1": "A1-Agree",
        "A2": "A2-Disagree",
    },
    "Q29": {
        "A1": "A1-Agree",
        "A2": "A2-Disagree",
    },
    "Q14": {
        "A1": "A1-Agree",
        "A2": "A2-Disagree",
        "A3": "A3-Does not apply",
    },
}


@dataclass
class QuestionInfo:
    row_idx: int            # 1-based
    question_id: str
    options_by_code: Dict[str, str]
    options_by_value: Dict[str, str]


def slugify(text: str, fallback: str = "item") -> str:
    cleaned = re.sub(r"[^0-9A-Za-z]+", "-", text).strip("-")
    return cleaned or fallback


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_json_export(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def render_conversation(messages: Iterable[dict]) -> str:
    lines: List[str] = []
    for msg in messages:
        role = msg.get("role", "").title() or "Unknown"
        content = msg.get("content", "").strip()
        if not content:
            continue
        lines.append(f"{role}: {content}")
        lines.append("")
    return "\n".join(lines).rstrip()


def clean_answer_token(raw: str) -> str:
    token = raw.strip()
    token = token.split()[0]
    token = token.rstrip(")")
    token = token.rstrip("*")
    token = token.rstrip(",")
    match = re.match(r"([A-Za-z0-9]+)", token)
    if match:
        return match.group(1)
    return token


def compute_dialog_metrics(messages: Iterable[dict]) -> Dict[str, int]:
    metrics = {
        "user_words": 0,
        "bot_words": 0,
        "user_utterances": 0,
        "bot_utterances": 0,
    }

    for msg in messages:
        role = (msg.get("role") or "").lower()
        content = (msg.get("content") or "").strip()
        if not content:
            continue

        word_count = len(re.findall(r"[A-Za-z0-9'-]+", content))
        if role in {"user", "human"}:
            metrics["user_words"] += word_count
            metrics["user_utterances"] += 1
        elif role in {"assistant", "bot"}:
            metrics["bot_words"] += word_count
            metrics["bot_utterances"] += 1

    return metrics


def parse_answer_map_from_message(text: str) -> Dict[str, str]:
    if "Q" not in text:
        return {}
    normalized = text.replace("\u00a0", " ")
    matches = ANSWER_TOKEN_RE.findall(normalized)
    if not matches:
        return {}
    answer_map: Dict[str, str] = {}
    for question_id, answer in matches:
        answer_map[question_id] = clean_answer_token(answer)
    return answer_map


def extract_best_answer_map(messages: Iterable[dict]) -> Dict[str, str]:
    best: Dict[str, str] = {}
    for msg in messages:
        answer_map = parse_answer_map_from_message(msg.get("content", ""))
        if len(answer_map) > len(best):
            best = answer_map
    return best


def load_template_rows(path: Path) -> List[List[str]]:
    rows: List[List[str]] = []
    with path.open("r", encoding="cp1252", newline="") as handle:
        reader = csv.reader(handle)
        rows = [row for row in reader]
    return rows


def parse_template(rows: List[List[str]]) -> tuple[List[QuestionInfo], Optional[int]]:
    questions: List[QuestionInfo] = []
    instruction_options: Dict[str, List[str]] = {}
    group_option_cache: Dict[str, List[str]] = {}
    next_question_options: List[str] = []
    next_question_remaining = 0
    first_question_row: Optional[int] = None

    for row_idx, row in enumerate(rows, start=1):
        question_text = row[QUESTION_COL].strip() if len(row) > QUESTION_COL else ""
        if not question_text:
            continue

        match = QUESTION_ID_RE.match(question_text)
        if match:
            num = match.group(1)
            letter = match.group(2)
            question_id = f"Q{num}{letter}"

            explicit_options = [
                cell.strip()
                for cell in row[OPTION_START_COL:]
                if cell.strip()
            ]

            option_sources: List[List[str]] = []
            if explicit_options:
                option_sources.append(explicit_options)

            key = f"{num}{letter}" if letter else num
            if key in instruction_options:
                option_sources.append(instruction_options[key])
            elif letter and f"{num}a" in instruction_options:
                option_sources.append(instruction_options[f"{num}a"])
            elif num in instruction_options:
                option_sources.append(instruction_options[num])
            elif letter and num in group_option_cache:
                option_sources.append(group_option_cache[num])

            if not explicit_options and next_question_remaining > 0 and next_question_options:
                option_sources.append(next_question_options)
                next_question_remaining -= 1

            options_by_code: Dict[str, str] = {}
            options_by_value: Dict[str, str] = {}
            for source in option_sources:
                for item in source:
                    if not item:
                        continue
                    if "-" in item:
                        code, text = item.split("-", 1)
                    else:
                        code, text = item, ""
                    code = code.strip()
                    text = text.strip()
                    if code:
                        options_by_code.setdefault(code, f"{code}-{text}" if text else code)
                    if text:
                        options_by_value.setdefault(text, f"{code}-{text}" if code else text)

            questions.append(
                QuestionInfo(
                    row_idx=row_idx,
                    question_id=question_id,
                    options_by_code=options_by_code,
                    options_by_value=options_by_value,
                )
            )

            if question_id in MANUAL_OPTION_OVERRIDES:
                override = MANUAL_OPTION_OVERRIDES[question_id]
                questions[-1].options_by_code.update(override)
                questions[-1].options_by_value.update(
                    {text.split("-", 1)[-1]: text for text in override.values() if "-" in text}
                )

            if first_question_row is None:
                first_question_row = row_idx

            if explicit_options:
                if letter:
                    group_option_cache.setdefault(num, explicit_options)
                else:
                    group_option_cache.setdefault(key, explicit_options)
            continue

        instruction_text = question_text
        option_groups = re.findall(r"\(([^)]+)\)", instruction_text)
        raw_options = [item.strip() for item in option_groups[-1].split(",")] if option_groups else []
        options: List[str] = []
        if raw_options:
            for idx, option in enumerate(raw_options, start=1):
                if option.startswith("A") and "-" in option:
                    options.append(option)
                else:
                    options.append(f"A{idx}-{option}")

        lowered = instruction_text.lower()
        range_match = re.search(r"questions?\s+(\d+)(?:-(\d+))?", instruction_text, re.IGNORECASE)
        if range_match and options:
            start = int(range_match.group(1))
            end = int(range_match.group(2) or start)
            for number in range(start, end + 1):
                instruction_options[str(number)] = options
        if options and ("next two questions" in lowered):
            next_question_options = options
            next_question_remaining = 2
        if options and ("has 4 parts" in lowered or "(a-d)" in lowered):
            num_match = re.search(r"(\d+)", instruction_text)
            if num_match:
                number = num_match.group(1)
                for suffix in ["a", "b", "c", "d"]:
                    instruction_options[f"{number}{suffix}"] = options

    return questions, first_question_row


def set_cell(row: List[str], col_idx: int, value: Optional[str]) -> None:
    while len(row) <= col_idx:
        row.append("")
    row[col_idx] = value or ""


def map_answer_to_value(answer: Optional[str], question: QuestionInfo) -> Optional[str]:
    if answer is None:
        return None
    answer = answer.strip()
    if not answer:
        return None
    if question.question_id in NUMERIC_QUESTIONS:
        if answer.startswith("A") and answer[1:].replace(".", "").isdigit():
            return answer[1:]
        if answer.replace(".", "").isdigit():
            return answer
    if answer in question.options_by_code:
        return question.options_by_code[answer]
    if answer in question.options_by_value:
        return question.options_by_value[answer]
    if answer.startswith("A") and answer[1:].isdigit():
        return answer[1:]
    return answer


def populate_template(
    template_rows: List[List[str]],
    question_infos: List[QuestionInfo],
    answers: Dict[str, str],
    first_question_row: Optional[int],
    user_identifier: str,
    chat_title: str,
) -> List[List[str]]:
    rows = deepcopy(template_rows)
    if first_question_row:
        row = rows[first_question_row - 1]
        set_cell(row, 0, user_identifier)
        set_cell(row, 1, chat_title)

    for question in question_infos:
        value = map_answer_to_value(answers.get(question.question_id), question)
        row = rows[question.row_idx - 1]
        set_cell(row, ANSWER_COL, value)

    return rows


def write_csv(path: Path, rows: List[List[str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)


def main() -> None:
    ensure_directory(CONVERSATIONS_DIR)
    ensure_directory(WORKBOOKS_DIR)

    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template CSV not found at {TEMPLATE_PATH}")

    template_rows = load_template_rows(TEMPLATE_PATH)
    for row_idx, col_idx in TEMPLATE_CELL_CLEARS:
        if row_idx < len(template_rows):
            set_cell(template_rows[row_idx], col_idx, "")
    question_infos, first_question_row = parse_template(template_rows)

    chats = load_json_export(CHAT_EXPORT)
    for index, chat in enumerate(chats, start=1):
        messages = chat.get("chat", {}).get("messages", [])
        conversation_text = render_conversation(messages)
        identifier = chat.get("user_id") or chat.get("id") or f"user-{index}"
        slug = slugify(identifier)
        convo_path = CONVERSATIONS_DIR / f"{index:02d}_{slug}.txt"
        convo_path.parent.mkdir(parents=True, exist_ok=True)
        convo_path.write_text(conversation_text, encoding="utf-8")

        metrics = compute_dialog_metrics(messages)
        answers = extract_best_answer_map(messages)
        if not answers:
            continue

        chat_title = chat.get("title") or chat.get("chat", {}).get("title") or slug
        populated_rows = populate_template(
            template_rows,
            question_infos,
            answers,
            first_question_row,
            identifier,
            chat_title,
        )

        for row_idx, header, metric_key in METRIC_ROWS:
            while len(populated_rows) <= row_idx:
                populated_rows.append([])
            metric_row = populated_rows[row_idx]
            set_cell(metric_row, 0, header)
            set_cell(metric_row, 1, str(metrics[metric_key]))

        out_name = f"{index:02d}_{slug}.csv"
        out_path = WORKBOOKS_DIR / out_name
        write_csv(out_path, populated_rows)


if __name__ == "__main__":
    main()
