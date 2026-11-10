# Political Economy Journal Watch

Independent cloud RSS snapshot for academic journal monitoring. Feeds are public metadata, not full-text access.

- The RSS parser is in `journal-watch/rss_parser.py`.
- GitHub Actions refreshes feed metadata daily; the ChatGPT literature briefing stays weekly.
- `journal-watch/public/latest_compact.json` contains the recent snapshot, while `latest.json` holds the full feed snapshot.
- RSS dates may lag publisher Online First dates and therefore require independent publisher/DOI verification.

No credentials or subscription access are stored here.
