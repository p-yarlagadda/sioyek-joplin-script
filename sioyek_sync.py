"""
sioyek_sync.py — Auto-sync Sioyek bookmarks & highlights to Joplin via the Data API.

Requirements:
  - Joplin desktop must be running with the Web Clipper enabled
    (Tools → Options → Web Clipper → Enable)

Usage:
  python sioyek_sync.py <sioyek_export.json> [interval_seconds]

  interval_seconds: how often to sync (default: 60, use 0 to run once)
"""

import json
import re
import sys
import time
import hashlib
from pathlib import Path
import urllib.request
import urllib.parse
import urllib.error


TOKEN = "PUT_YOUR_TOKEN_HERE"
NOTEBOOK = "Sioyek"
BASE_URL = "http://localhost:41184"


def api(method, endpoint, data=None, params=None):
    query = {"token": TOKEN}
    if params:
        query.update(params)
    url = f"{BASE_URL}{endpoint}?" + urllib.parse.urlencode(query)
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, method=method)
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"API error {e.code}: {e.read().decode()}")


def ping():
    try:
        with urllib.request.urlopen(f"{BASE_URL}/ping", timeout=3) as r:
            return r.read().decode().strip() == "JoplinClipperServer"
    except Exception:
        return False


def get_or_create_notebook(name):
    for folder in api("GET", "/folders").get("items", []):
        if folder["title"].lower() == name.lower():
            return folder["id"]
    return api("POST", "/folders", data={"title": name})["id"]


def get_notes_in_notebook(notebook_id):
    result = api("GET", f"/folders/{notebook_id}/notes", params={"fields": "id,title,body"})
    return {n["title"]: n for n in result.get("items", [])}


def clean_title(path):
    return Path(path).stem


def split_inline_note(text):
    """Split 'quote {inline note}' into (quote, note). Returns (text, None) if no braces."""
    match = re.search(r'\{(.+?)\}\s*$', text, re.DOTALL)
    if match:
        note = match.group(1).strip()
        quote = text[:match.start()].strip()
        return quote, note
    return text.strip(), None


def format_body(doc):
    bookmarks = sorted(doc.get("bookmarks", []), key=lambda b: b.get("y_offset", 0))
    highlights = sorted(doc.get("highlights", []), key=lambda h: h.get("selection_begin_y", 0))
    lines = []

    if bookmarks:
        lines.append("## Bookmarks")
        lines.append("")
        for bm in bookmarks:
            raw = bm.get("description", "").strip()
            if not raw:
                continue
            quote, note = split_inline_note(raw)
            lines.append(f"> {quote}")
            if note:
                lines.append("")
                lines.append(f"*{note}*")
            lines.append("")

    if highlights:
        if bookmarks:
            lines.append("")
        lines.append("## Highlights")
        lines.append("")
        for hl in highlights:
            text = hl.get("description", "").strip()
            if not text:
                continue
            lines.append(f"> {text}")
            lines.append("")

    if not bookmarks and not highlights:
        lines.append("*No annotations recorded.*")

    return "\n".join(lines)


def has_annotations(doc):
    return bool(doc.get("bookmarks")) or bool(doc.get("highlights"))


def checksum(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def sync(json_path):
    print(f"[sync] {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    documents = data.get("documents", [])
    if not documents:
        print("[sync] No documents found.")
        return

    notebook_id = get_or_create_notebook(NOTEBOOK)
    existing = get_notes_in_notebook(notebook_id)
    created = updated = skipped = 0

    for doc in documents:
        if not has_annotations(doc):
            continue
        title = clean_title(doc.get("path", "Untitled"))
        body = format_body(doc)

        if title in existing:
            note = existing[title]
            if checksum(note.get("body", "")) != checksum(body):
                api("PUT", f"/notes/{note['id']}", data={"body": body})
                print(f"  ↻ Updated:  {title}")
                updated += 1
            else:
                skipped += 1
        else:
            api("POST", "/notes", data={
                "title": title,
                "body": body,
                "parent_id": notebook_id,
                "markup_language": 1
            })
            print(f"  + Created:  {title}")
            created += 1

    print(f"[sync] {created} created, {updated} updated, {skipped} unchanged\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python sioyek_sync.py <sioyek_export.json> [interval_seconds]")
        sys.exit(1)

    json_path = Path(sys.argv[1]).resolve()
    if not json_path.exists():
        print(f"Error: File not found: {json_path}")
        sys.exit(1)

    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60

    if not ping():
        print("Error: Could not reach Joplin. Make sure it's running with Web Clipper enabled.")
        sys.exit(1)

    print(f"Connected to Joplin ✓  (notebook: {NOTEBOOK})\n")

    if interval == 0:
        sync(json_path)
    else:
        while True:
            try:
                sync(json_path)
                print(f"Next sync in {interval}s... (Ctrl+C to stop)")
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\nStopped.")
                break


if __name__ == "__main__":
    main()
