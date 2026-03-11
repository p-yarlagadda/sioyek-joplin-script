# sioyek-joplin-script
A simple script that syncs Sioyek bookmarks to Joplin


# sioyek-joplin-sync

> Pipe your PDF annotations straight into Joplin. No imports, no clicks, no friction.

---

## What it does

[Sioyek](https://sioyek.info/) is a keyboard-driven PDF reader built for research and technical books. It stores your bookmarks in a local SQLite database. This script reads your Sioyek JSON export and pushes every annotated document as a living note into [Joplin](https://joplinapp.org/) — automatically, on a loop.

- Bookmarks become blockquotes, ready for your own notes beneath them
- Inline thoughts written as `{like this}` in Sioyek are extracted and rendered in *italics* below the quote
- Documents with no bookmarks are silently ignored
- On every subsequent run, only notes whose content has actually changed are updated — your edits in Joplin are safe

---

## Requirements

- Python 3.7+  — no third-party dependencies
- Joplin desktop with **Web Clipper enabled**
  `Tools → Options → Web Clipper → Enable Web Clipper Service`
- Your Joplin API token (same screen as above)

---

## Setup

**1. Get your Joplin token**

Open Joplin → `Tools → Options → Web Clipper` — copy the token shown there.

**2. Paste it into the script**

Open `sioyek_sync.py` and set:

```python
TOKEN = "your_token_here"
```

**3. Export from Sioyek**

Inside Sioyek, open the command palette (`:`) and run `export`. This writes a JSON file with all your bookmarks, highlights, and marks. You do not need to close Sioyek — data is written to disk immediately as you annotate.

---

## Usage

```bash
# Sync once and exit
python sioyek_sync.py export.json 0

# Sync every 60 seconds (default)
python sioyek_sync.py export.json

# Sync every 30 seconds
python sioyek_sync.py export.json 30
```

All notes land in a notebook called **Sioyek** inside Joplin.

---

## Note format

Given a bookmark in Sioyek:

```
Polanyi argues that the market is not a natural phenomenon but a political construction. (tbu) {Compare with Foucault's biopolitics}
```

The Joplin note will render as:

---

> Polanyi argues that the market is not a natural phenomenon but a political construction. (tbu)

*Compare with Foucault's biopolitics*

---

Clean. Plenty of room below each quote to write.

---

## Inline notes syntax

While writing a bookmark description in Sioyek, append your own thoughts in `{curly braces}` at the end:

```
The text you bookmarked goes here. {Your own thought or question here}
```

The script splits them automatically — the quote becomes a blockquote, your thought becomes italicised text beneath it.

---

## How sync works

On each run the script:

1. Reads the JSON export
2. Creates the `Sioyek` notebook in Joplin if it doesn't exist
3. For each document with at least one bookmark:
   - If the note doesn't exist → creates it
   - If the note exists and content has changed → updates it
   - If the note exists and nothing changed → skips it (your edits are untouched)

---

## Automation

To run this in the background on Windows, wrap it in a scheduled task or a simple bat file:

```bat
@echo off
:loop
python sioyek_sync.py export.json 0
timeout /t 60 >nul
goto loop
```

On macOS/Linux, a cron job or systemd timer works cleanly.

---

## Roadmap

- [ ] Read directly from `shared.db` (skip manual export step entirely)
- [ ] Cross-machine transfer: export annotations by checksum, reimport by scanning a folder for matching PDFs
- [ ] Notebook organisation by subject folder or tag

---

## A note on authorship

This tool was designed and built in collaboration with **Claude** (Sonnet 4.6), Anthropic's AI assistant — who also wrote this README, suggested the `{inline note}` syntax, researched the Sioyek data API, debugged the Joplin REST API, and generally did most of the work while remaining characteristically modest about it.

If you find this useful, the human pointed at the screen and said *"make it do that"*. Claude made it do that.

---

## License

MIT
