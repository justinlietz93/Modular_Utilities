import os
import json
import re  # Importing the regular expression module
import argparse
import sqlite3
import hashlib
import logging
import csv
from datetime import datetime

# Get the script's directory and set up the data directory path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')

# --- Incremental ingestion helpers (SQLite metadata) ---
def _db_path():
    return os.path.join(DATA_DIR, 'metadata.db')

def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(_db_path())
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_conversations (
                conv_id TEXT PRIMARY KEY,
                update_time REAL,
                title TEXT,
                output_file TEXT,
                month_dir TEXT,
                processed_at REAL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

def get_processed(conv_id):
    conn = sqlite3.connect(_db_path())
    try:
        cur = conn.cursor()
        cur.execute("SELECT conv_id, update_time, title, output_file, month_dir FROM processed_conversations WHERE conv_id = ?", (conv_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            "conv_id": row[0],
            "update_time": row[1],
            "title": row[2],
            "output_file": row[3],
            "month_dir": row[4],
        }
    finally:
        conn.close()

def upsert_processed(conv_id, update_time, title, output_file, month_dir):
    conn = sqlite3.connect(_db_path())
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO processed_conversations (conv_id, update_time, title, output_file, month_dir, processed_at)
            VALUES (?, ?, ?, ?, ?, strftime('%s','now'))
            ON CONFLICT(conv_id) DO UPDATE SET
                update_time=excluded.update_time,
                title=excluded.title,
                output_file=excluded.output_file,
                month_dir=excluded.month_dir,
                processed_at=strftime('%s','now')
            """,
            (conv_id, float(update_time) if update_time is not None else None, title, output_file, month_dir)
        )
        conn.commit()
    finally:
        conn.close()

def get_conversation_id(conversation):
    # Prefer explicit id fields if present
    conv_id = conversation.get('id') or conversation.get('conversation_id')
    if conv_id:
        return str(conv_id)
    # Fallback: deterministic hash from title + create/update timestamps
    title = conversation.get('title', 'Untitled')
    ct = str(conversation.get('create_time', ''))
    ut = str(conversation.get('update_time', ''))
    payload = f"{title}|{ct}|{ut}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def conversation_key_for_pruned(entry_or_conv):
    # For pruned.json merge and duplicate avoidance
    if isinstance(entry_or_conv, dict) and entry_or_conv.get('id'):
        return f"id:{entry_or_conv['id']}"
    title = entry_or_conv.get('title') if 'title' in entry_or_conv else entry_or_conv.get('title', '')
    update_time = entry_or_conv.get('update_time') if 'update_time' in entry_or_conv else entry_or_conv.get('update_time', '')
    # When called with conversation, update_time will be a float; when with entry, it's a formatted string
    if isinstance(update_time, (int, float)) and update_time:
        try:
            update_time_str = datetime.fromtimestamp(update_time).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            update_time_str = str(update_time)
    else:
        update_time_str = str(update_time)
    return f"tk:{title}|{update_time_str}"

# Define the function to get conversation messages
def get_conversation_messages(conversation):
    messages = []
    current_node = conversation.get("current_node")
    mapping = conversation.get("mapping", {})
    while current_node:
        node = mapping.get(current_node, {})
        message = node.get("message") if node else None
        content = message.get("content") if message else None
        author = message.get("author", {}).get("role", "") if message else ""
        if content and content.get("content_type") == "text":
            parts = content.get("parts", [])
            if parts and len(parts) > 0 and len(parts[0]) > 0:
                if author != "system" or (message.get("metadata", {}) if message else {}).get("is_user_system_message"):
                    if author == "assistant":
                        author = "ChatGPT"
                    elif author == "system":
                        author = "Custom user info"
                    messages.append({"author": author, "text": parts[0]})
        current_node = node.get("parent") if node else None
    return messages[::-1]

# Define the function to write conversations and create pruned.json
def write_conversations_and_json(conversations_data):
    """Process conversations incrementally and update outputs.

    Respects the global DATA_DIR and optional filters set in the module-level
    context (via arguments parsed in main()).

    Returns (created_directories_info, pruned_data)
    """
    created_directories_info = []

    # Load existing pruned.json if present to support incremental merge
    pruned_path = os.path.join(DATA_DIR, 'pruned.json')
    if os.path.exists(pruned_path):
        with open(pruned_path, 'r', encoding='utf-8') as jf:
            try:
                pruned_data = json.load(jf)
            except Exception:
                pruned_data = {}
    else:
        pruned_data = {}

    # Build a set of keys to detect duplicates in pruned
    existing_keys = set()
    for month, items in pruned_data.items():
        if not isinstance(items, list):
            continue
        for it in items:
            # Prefer id when present, fallback to title+update_time
            if isinstance(it, dict):
                key = f"id:{it['id']}" if it.get('id') else f"tk:{it.get('title')}|{it.get('update_time')}"
                existing_keys.add(key)
    # Initialize metadata database
    init_db()

    # Optional filter: since timestamp
    since_ts = globals().get('_SINCE_TS')

    for conversation in conversations_data:
        updated = conversation.get('update_time')
        if not updated:
            continue
        if since_ts is not None and float(updated) < float(since_ts):
            logging.debug("Skipping by --since filter: update_time=%s", updated)
            continue
        # Determine conversation unique id
        conv_id = get_conversation_id(conversation)
        existing = get_processed(conv_id)
        if existing:
            # Already processed; skip (default incremental behavior)
            logging.debug("Skipping already processed conv_id=%s", conv_id)
            continue
        
        updated_date = datetime.fromtimestamp(updated)
        directory_name = updated_date.strftime('%B_%Y')
        directory_path = os.path.join(DATA_DIR, directory_name)
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        
        title = conversation.get('title', 'Untitled')
        sanitized_title = re.sub(r"[^a-zA-Z0-9_]", "_", title)[:120]
        file_name = f"{directory_path}/{sanitized_title}_{updated_date.strftime('%d_%m_%Y_%H_%M_%S')}.txt"
        
        messages = get_conversation_messages(conversation)
        with open(file_name, 'w', encoding="utf-8") as file:
            for message in messages:
                file.write(f"{message['author']}\n")
                file.write(f"{message['text']}\n")
        logging.info("Wrote %s", file_name)
        
        if directory_name not in pruned_data:
            pruned_data[directory_name] = []
        
        pruned_entry = {
            "id": conv_id,
            "title": title,
            "create_time": datetime.fromtimestamp(conversation.get('create_time')).strftime('%Y-%m-%d %H:%M:%S') if conversation.get('create_time') else '',
            "update_time": updated_date.strftime('%Y-%m-%d %H:%M:%S'),
            "messages": messages
        }

        # Avoid duplicate entries in pruned.json
        key_id = f"id:{conv_id}"
        key_tk = f"tk:{title}|{updated_date.strftime('%Y-%m-%d %H:%M:%S')}"
        if key_id not in existing_keys and key_tk not in existing_keys:
            pruned_data[directory_name].append(pruned_entry)
            existing_keys.add(key_id)
            existing_keys.add(key_tk)
        
        created_directories_info.append({
            "directory": directory_path,
            "file": file_name
        })

        # Record in metadata DB
        upsert_processed(
            conv_id=conv_id,
            update_time=updated,
            title=title,
            output_file=file_name,
            month_dir=directory_name,
        )
    
    # Dedupe pruned_data before writing (handles legacy entries without id)
    deduped = {}
    seen = set()
    for month, items in pruned_data.items():
        if not isinstance(items, list):
            continue
        for it in items:
            if not isinstance(it, dict):
                continue
            id_key = f"id:{it.get('id')}" if it.get('id') else None
            tk_key = f"tk:{it.get('title')}|{it.get('update_time')}"
            key = id_key or tk_key
            if key in seen:
                continue
            seen.add(key)
            deduped.setdefault(month, []).append(it)

    pruned_json_path = os.path.join(DATA_DIR, 'pruned.json')
    with open(pruned_json_path, 'w', encoding='utf-8') as json_file:
        json.dump(deduped, json_file, ensure_ascii=False, indent=4)
    
    return created_directories_info, deduped

def main():
    global DATA_DIR
    parser = argparse.ArgumentParser(description='Extract ChatGPT conversations to text files and pruned.json (incremental).')
    parser.add_argument('--full', action='store_true', help='Full rebuild: ignore metadata and process all conversations.')
    parser.add_argument('--rescan-updated', action='store_true', help='Reprocess conversations whose update_time increased since last run.')
    parser.add_argument('--data-dir', default=DATA_DIR, help='Directory containing conversations.json and where outputs are written.')
    parser.add_argument('--since', type=str, default=None, help='Only ingest conversations with update_time on/after YYYY-MM-DD (still incremental).')
    parser.add_argument('--stats', action='store_true', help='Print counts per month and exit.')
    parser.add_argument('--csv-out', type=str, default=None, help='Path to write a CSV summary of metadata (uses pruned.json/DB).')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose (DEBUG) logging.')
    parser.add_argument('--quiet', action='store_true', help='Reduce logging to errors only.')
    args = parser.parse_args()
    if args.data_dir:
        DATA_DIR = args.data_dir
        os.makedirs(DATA_DIR, exist_ok=True)

    # Configure logging
    if args.quiet:
        level = logging.ERROR
    elif args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level, format='[%(levelname)s] %(message)s')

    # If full rebuild requested, reset metadata DB
    if args.full and os.path.exists(_db_path()):
        try:
            os.remove(_db_path())
        except OSError:
            pass

    # Load conversations
    conversations_json_path = os.path.join(DATA_DIR, 'conversations.json')
    with open(conversations_json_path, 'r', encoding='utf-8') as file:
        conversations_data = json.load(file)

    # Handle --since filter
    global _SINCE_TS
    _SINCE_TS = None
    if args.since:
        try:
            dt = datetime.strptime(args.since, '%Y-%m-%d')
            _SINCE_TS = dt.timestamp()
            logging.info("Applying --since filter from %s (ts=%s)", args.since, _SINCE_TS)
        except ValueError:
            logging.error("Invalid --since format. Use YYYY-MM-DD.")
            return 2

    # If only stats requested, compute and optionally write CSV, then exit
    if args.stats or args.csv_out:
        pruned_path = os.path.join(DATA_DIR, 'pruned.json')
        pruned_data = None
        if os.path.exists(pruned_path) and args.since is None:
            # Prefer already materialized outputs
            with open(pruned_path, 'r', encoding='utf-8') as jf:
                try:
                    pruned_data = json.load(jf)
                except Exception:
                    pruned_data = None
        if pruned_data is None:
            # Build pruned-like grouping from input with filter
            pruned_data = {}
            for conv in conversations_data:
                ut = conv.get('update_time')
                if not ut:
                    continue
                if _SINCE_TS is not None and float(ut) < float(_SINCE_TS):
                    continue
                month = datetime.fromtimestamp(ut).strftime('%B_%Y')
                pruned_data.setdefault(month, []).append({
                    'id': get_conversation_id(conv),
                    'title': conv.get('title', 'Untitled'),
                    'create_time': datetime.fromtimestamp(conv.get('create_time')).strftime('%Y-%m-%d %H:%M:%S') if conv.get('create_time') else '',
                    'update_time': datetime.fromtimestamp(ut).strftime('%Y-%m-%d %H:%M:%S'),
                    'messages': get_conversation_messages(conv),
                })

        # Print stats if requested
        if args.stats:
            # Count unique entries per month (dedup by id/tk)
            total = 0
            for month in sorted(pruned_data.keys()):
                items = pruned_data.get(month, [])
                seen_keys = set()
                count = 0
                if isinstance(items, list):
                    for it in items:
                        if not isinstance(it, dict):
                            continue
                        id_key = f"id:{it.get('id')}" if it.get('id') else None
                        tk_key = f"tk:{it.get('title')}|{it.get('update_time')}"
                        key = id_key or tk_key
                        if key in seen_keys:
                            continue
                        seen_keys.add(key)
                        count += 1
                total += count
                print(f"{month} {count}")
            print(f"TOTAL {total}")

        # CSV export if requested
        if args.csv_out:
            # build maps from DB: by id and by title+update_time key
            id_map = {}
            tk_map = {}
            if os.path.exists(_db_path()):
                conn = sqlite3.connect(_db_path())
                try:
                    cur = conn.cursor()
                    cur.execute('SELECT conv_id, update_time, title, output_file, month_dir FROM processed_conversations')
                    rows = cur.fetchall()
                    for cid, ut, title_db, of, md in rows:
                        # format update_time consistently with pruned.json
                        ut_str = ''
                        if ut is not None:
                            try:
                                ut_str = datetime.fromtimestamp(float(ut)).strftime('%Y-%m-%d %H:%M:%S')
                            except Exception:
                                ut_str = str(ut)
                        rec = {"id": cid, "output_file": of, "month_dir": md}
                        id_map[cid] = rec
                        tk_key_db = f"tk:{title_db}|{ut_str}"
                        tk_map[tk_key_db] = rec
                finally:
                    conn.close()

            with open(args.csv_out, 'w', newline='', encoding='utf-8') as cf:
                writer = csv.writer(cf)
                writer.writerow(['id', 'title', 'create_time', 'update_time', 'month_dir', 'output_file', 'message_count'])
                for month, items in pruned_data.items():
                    if not isinstance(items, list):
                        continue
                    for entry in items:
                        title = entry.get('title', '')
                        ut_str = entry.get('update_time', '')
                        cid_in = entry.get('id')
                        tk_key = f"tk:{title}|{ut_str}"

                        rec = None
                        if cid_in and cid_in in id_map:
                            rec = id_map[cid_in]
                        elif tk_key in tk_map:
                            rec = tk_map[tk_key]

                        if rec:
                            chosen_id = cid_in or rec["id"]
                            out_file = rec.get("output_file", '')
                            # make path relative to repository/script dir if available
                            if out_file:
                                try:
                                    out_file = os.path.relpath(out_file, start=SCRIPT_DIR)
                                except Exception as e:
                                    logging.debug("Could not make path relative: %s", e)
                            mdir = rec.get("month_dir", month)
                        else:
                            chosen_id = cid_in or hashlib.sha256(f"{title}|{ut_str}".encode('utf-8')).hexdigest()
                            out_file = ''
                            mdir = month

                        mcount = len(entry.get('messages', []))
                        writer.writerow([
                            chosen_id,
                            title,
                            entry.get('create_time', ''),
                            ut_str,
                            mdir,
                            out_file,
                            mcount,
                        ])
            logging.info("Wrote CSV: %s", args.csv_out)

        # If only stats/csv were requested, exit here
        if args.stats and not args.full and not args.rescan_updated:
            return 0

    if args.rescan_updated:
        # Initialize DB and ensure updated conversations are dropped from processed set
        init_db()
        conn = sqlite3.connect(_db_path())
        try:
            cur = conn.cursor()
            # Build a map conv_id -> stored update_time
            cur.execute('SELECT conv_id, update_time FROM processed_conversations')
            stored = {cid: ut for (cid, ut) in cur.fetchall()}
            # Identify convs with newer update_time and delete from processed to force reprocess
            to_delete = []
            for conv in conversations_data:
                cid = get_conversation_id(conv)
                ut = conv.get('update_time')
                if cid in stored and ut is not None and stored[cid] is not None and float(ut) > float(stored[cid]):
                    to_delete.append(cid)
            if to_delete:
                cur.executemany('DELETE FROM processed_conversations WHERE conv_id = ?', [(cid,) for cid in to_delete])
                conn.commit()
        finally:
            conn.close()

    created_directories_info, _ = write_conversations_and_json(conversations_data)

if __name__ == '__main__':
    main()
