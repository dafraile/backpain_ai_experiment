#!/usr/bin/env python3
"""
Match conversation files to crossover study users.

Mapping chain:
  Filename UUID → Open WebUI user (users.csv) → email
  Email → chatbot_credential.external_username → assigned_user_id
  assigned_user_id → crossover.db user (username, group)

Usage:
  python3 match_conversations.py

Output:
  conversation_mapping.csv - All matched conversations with user info
"""

import os
import re
import csv
import json
import sqlite3
import pandas as pd
from pathlib import Path

# Paths (relative to script location)
SCRIPT_DIR = Path(__file__).parent
CONVERSATIONS_DIR = SCRIPT_DIR / "conversations"
USERS_CSV = SCRIPT_DIR / "users.csv"
CROSSOVER_DB = SCRIPT_DIR / "crossover.db"
EXCEL_FILE = SCRIPT_DIR / "crossover_exportMP.xlsx"
OUTPUT_CSV = SCRIPT_DIR / "conversation_mapping.csv"
OUTPUT_JSON = SCRIPT_DIR / "conversation_mapping.json"


def load_openwebui_users():
    """Load Open WebUI users: UUID → {name, email}"""
    users = {}
    with open(USERS_CSV, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            users[row['id']] = {'name': row['name'], 'email': row['email'], 'role': row['role']}
    return users


def load_crossover_data():
    """Load crossover.db data: credentials and users"""
    conn = sqlite3.connect(CROSSOVER_DB)

    # chatbot_credential: email → assigned_user_id
    creds = pd.read_sql("SELECT external_username, assigned_user_id FROM chatbot_credential", conn)
    email_to_userid = dict(zip(creds['external_username'], creds['assigned_user_id']))

    # users: id → {username, group}
    users = pd.read_sql('SELECT id, username, "group" FROM user', conn)
    userid_to_info = {
        int(row['id']): {'username': row['username'], 'group': row['group']}
        for _, row in users.iterrows()
    }

    conn.close()
    return email_to_userid, userid_to_info


def load_excel_mappings():
    """Load manual Conversation# → UserID mappings from Excel"""
    df = pd.read_excel(EXCEL_FILE)
    mappings = {}

    for _, row in df.iterrows():
        conv_num = row.get('Conversation#')
        user_id = row.get('UserID')

        if pd.notna(conv_num) and pd.notna(user_id):
            try:
                conv_num = int(conv_num)
                user_id = int(user_id)
                mappings[conv_num] = user_id
            except (ValueError, TypeError):
                continue

    return mappings


def parse_conversation_files():
    """Parse conversation filenames: {conv_num}_{uuid}.txt"""
    files = []

    for filename in os.listdir(CONVERSATIONS_DIR):
        if not filename.endswith('.txt'):
            continue

        match = re.match(r'(\d+)_([a-f0-9-]+)\.txt', filename)
        if match:
            files.append({
                'filename': filename,
                'conv_num': int(match.group(1)),
                'openwebui_uuid': match.group(2)
            })

    return sorted(files, key=lambda x: x['conv_num'])


def match_conversations():
    """Main matching logic"""
    # Load all data sources
    print("Loading data sources...")
    owui_users = load_openwebui_users()
    email_to_userid, userid_to_info = load_crossover_data()
    excel_mappings = load_excel_mappings()
    conv_files = parse_conversation_files()

    print(f"  Open WebUI users: {len(owui_users)}")
    print(f"  Crossover credentials: {len(email_to_userid)}")
    print(f"  Crossover users: {len(userid_to_info)}")
    print(f"  Excel mappings: {len(excel_mappings)}")
    print(f"  Conversation files: {len(conv_files)}")

    # Match each file
    results = []
    matched = 0
    unmatched = 0

    for conv in conv_files:
        result = {
            'filename': conv['filename'],
            'conv_num': conv['conv_num'],
            'openwebui_uuid': conv['openwebui_uuid'],
            'openwebui_name': None,
            'openwebui_email': None,
            'crossover_user_id': None,
            'crossover_username': None,
            'crossover_group': None,
            'match_method': None,
            'match_status': 'unmatched'
        }

        # Get Open WebUI user info from UUID
        if conv['openwebui_uuid'] in owui_users:
            owui = owui_users[conv['openwebui_uuid']]
            result['openwebui_name'] = owui['name']
            result['openwebui_email'] = owui['email']

            # Try to find crossover user via email
            if owui['email'] in email_to_userid:
                user_id = int(email_to_userid[owui['email']])
                result['crossover_user_id'] = user_id
                result['match_method'] = 'uuid_email_chain'

                if user_id in userid_to_info:
                    info = userid_to_info[user_id]
                    result['crossover_username'] = info['username']
                    result['crossover_group'] = info['group']
                    result['match_status'] = 'matched'
                    matched += 1
                else:
                    result['match_status'] = 'partial_no_user_info'
                    unmatched += 1
            else:
                result['match_status'] = 'no_credential_match'
                unmatched += 1
        else:
            result['match_status'] = 'uuid_not_found'
            unmatched += 1

        # Check against Excel manual mapping for verification
        if conv['conv_num'] in excel_mappings:
            excel_user_id = excel_mappings[conv['conv_num']]
            result['excel_user_id'] = excel_user_id

            if excel_user_id in userid_to_info:
                info = userid_to_info[excel_user_id]
                result['excel_username'] = info['username']
                result['excel_group'] = info['group']

            if result['crossover_user_id'] and result['crossover_user_id'] != excel_user_id:
                result['match_status'] = 'NEEDS_REVIEW'
                print(f"  REVIEW NEEDED: {conv['filename']}")
                print(f"    Auto (UUID chain): user_id={result['crossover_user_id']}, username={result['crossover_username']}")
                print(f"    Excel (manual):    user_id={excel_user_id}, username={result.get('excel_username', 'N/A')}")

        results.append(result)

    print(f"\nMatching complete:")
    print(f"  Matched: {matched}")
    print(f"  Unmatched: {unmatched}")

    return results


def save_results(results):
    """Save results to CSV and JSON"""
    # CSV
    fieldnames = [
        'filename', 'conv_num', 'openwebui_uuid', 'openwebui_name', 'openwebui_email',
        'crossover_user_id', 'crossover_username', 'crossover_group',
        'excel_user_id', 'excel_username', 'excel_group',
        'match_method', 'match_status'
    ]

    with open(OUTPUT_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)

    print(f"\nSaved: {OUTPUT_CSV}")

    # JSON
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Saved: {OUTPUT_JSON}")


def print_summary(results):
    """Print summary of results"""
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    # Group by status
    by_status = {}
    for r in results:
        status = r['match_status']
        by_status.setdefault(status, []).append(r)

    for status, items in sorted(by_status.items()):
        print(f"\n{status}: {len(items)}")
        if status != 'matched' and len(items) <= 10:
            for item in items:
                print(f"  - {item['filename']}")


if __name__ == '__main__':
    print("Conversation Matcher")
    print("="*60)

    results = match_conversations()
    save_results(results)
    print_summary(results)
