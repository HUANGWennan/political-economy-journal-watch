"""Accumulate and deduplicate public RSS records across daily runs.

This is an append-preserving archive, not an assertion about first-online
publication dates. It never removes records just because a feed omits them.
"""
import datetime as dt
import hashlib
import html
import json
import pathlib
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

HISTORY_FILE = pathlib.Path(__file__).resolve().parent / "public" / "history.json"
DISCOVERIES_FILE = HISTORY_FILE.parent / "discoveries.json"
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s<>\"']+", re.I)


def normalized_doi(value):
    if not value:
        return ""
    value = html.unescape(str(value)).strip()
    match = DOI_RE.search(value)
    return match.group(0).rstrip(".,;:)]}>").lower() if match else ""


def normalized_url(value):
    if not value:
        return ""
    try:
        parsed = urlsplit(html.unescape(str(value)).strip())
        if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
            return ""
        host = parsed.hostname.lower()
        path = re.sub(r"/+$", "", parsed.path) or "/"
        query = urlencode(sorted(
            (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if not (k.lower().startswith("utm_") or k.lower() in ("fbclid", "gclid"))
        ))
        return urlunsplit(("https", host, path, query, ""))
    except ValueError:
        return ""


def normalized_title(value):
    value = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.findall(r"\w+", value, flags=re.UNICODE))


def aliases(record):
    journal = (record.get("journal") or "").strip().casefold()
    if not journal:
        raise ValueError("History entry missing journal")
    result = []
    doi = normalized_doi(record.get("doi"))
    if doi:
        result.append(journal + "|doi:" + doi)
    for key in ("link", "identifier"):
        v = normalized_url(record.get(key))
        if v:
            result.append(journal + "|url:" + v)
    title = normalized_title(record.get("title"))
    if title:
        result.append(journal + "|title:" + title)
    return result


def _make_id(row):
    keys = aliases(row)
    return hashlib.sha256((keys[0] if keys else row["journal"] + "|" + row["title"]).encode("utf-8")).hexdigest()[:24]


def _match(history, row):
    """Conservative lookup; distinct explicit DOIs must never merge by title."""
    candidate_keys = aliases(row)
    incoming_doi = normalized_doi(row.get("doi"))
    for key in candidate_keys:
        for old in history:
            old_doi = normalized_doi(old.get("doi"))
            if incoming_doi and old_doi and incoming_doi != old_doi:
                continue
            if key in aliases(old):
                return old
    return None


def update_history(snapshot, now=None, history_path=None, discoveries_path=None):
    """Merge ONLY successfully fetched RSS items, atomically within a Git commit.

    No existing article is ever removed. A bad history file raises immediately,
    preventing the workflow from silently resetting prior observations.
    """
    now = now or dt.datetime.now(dt.timezone.utc)
    stamp = now.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    history_path = pathlib.Path(history_path or HISTORY_FILE)
    discoveries_path = pathlib.Path(discoveries_path or DISCOVERIES_FILE)
    if history_path.exists():
        history = json.loads(history_path.read_text(encoding="utf-8"))
        if history.get("schema_version") != 1 or not isinstance(history.get("articles"), list):
            raise ValueError("Unexpected history schema: refusing to overwrite archive")
    else:
        history = {"schema_version": 1, "created_utc": stamp, "articles": []}
    stored = history["articles"]
    prior_count = len(stored)
    additions = []
    per_feed = []
    for feed in snapshot.get("feeds", []):
        journal = feed["journal"]
        if feed.get("status") != "ok":
            per_feed.append({"journal": journal, "status": feed.get("status"),
                             "new": 0, "reason": "not a fresh successful fetch"})
            continue
        added = 0
        for item in feed.get("items", []):
            if not item.get("title"):
                continue
            row = dict(item, journal=journal)
            found = _match(stored, row)
            if found is None:
                record = dict(row, id=_make_id(row),
                              first_seen_utc=stamp, last_seen_utc=stamp)
                record["doi"] = normalized_doi(record.get("doi")) or None
                stored.append(record)
                additions.append(record)
                added += 1
            else:
                found["last_seen_utc"] = stamp
                if not found.get("doi"):
                    found["doi"] = normalized_doi(row.get("doi")) or None
                for key in ("title", "link", "identifier", "summary_excerpt", "raw_date"):
                    if row.get(key):
                        found[key] = row[key]
                if row.get("feed_date"):
                    found["feed_date"] = row["feed_date"]
        per_feed.append({"journal": journal, "status": "ok", "new": added})
    if len(stored) < prior_count:
        raise AssertionError("Historical corpus size decreased")
    # Archive remains the source of truth; indexes are derived in every run.
    history["updated_utc"] = stamp
    history["total_articles"] = len(stored)
    history["new_this_run"] = len(additions)
    history["new_by_journal"] = {x["journal"]: x["new"] for x in per_feed}
    history["note"] = "RSS observations, not verified first-online dates. Never treat first_seen_utc as publication date."
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    cutoff = (now - dt.timedelta(days=45)).isoformat().replace("+00:00", "Z")
    recent = [x for x in stored if x.get("first_seen_utc", "") >= cutoff]
    recent.sort(key=lambda x: x["first_seen_utc"], reverse=True)
    compact = lambda a: {k: a.get(k) for k in (
        "id", "journal", "title", "doi", "link", "feed_date", "first_seen_utc"
    )}
    discoveries = {
        "schema_version": 1, "generated_utc": stamp,
        "total_historical_articles": len(stored), "new_this_run": len(additions),
        "new_by_journal": history["new_by_journal"],
        "feeds": per_feed,
        "recent_window_days": 45,
        "recent_discoveries": [compact(x) for x in recent],
        "note": "Observed in RSS; verify publisher first-online dates and deduplicate against previous ChatGPT reports.",
    }
    discoveries_path.write_text(json.dumps(discoveries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("HISTORY: total=%s, newly_observed=%s" % (len(stored), len(additions)), flush=True)
    return discoveries
