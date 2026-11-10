# Political Economy Journal Watch

Cloud-based RSS ingestion and permanent bibliographic history for eight English-language academic journals. The ChatGPT Political Economy Journal Watch runs weekly and independently checks **14 journals**.

## Daily cloud ingestion
The GitHub Actions workflow [Journal RSS Cloud Snapshot](.github/workflows/journal-rss-cloud.yml) runs every day at 07:17 UTC (and on parser/workflow/test changes). It requires no Mac, device, credentials, or paid API.

* [`journal-watch/rss_parser.py`](journal-watch/rss_parser.py): parses RSS 2.0, Atom, and namespaced RDF/RSS 1.0; reports feed errors and stale dates.
* [`journal-watch/history.py`](journal-watch/history.py): merges newly observed records into the cumulative corpus, deduplicating by DOI, canonical URL, or article title within the journal. The merge never deletes previously recorded articles when feeds rotate or fail.
* [`journal-watch/public/history.json`](journal-watch/public/history.json): **permanent cumulative RSS bibliographic archive**, recording `first_seen_utc` and `last_seen_utc`. The initial run imports all existing RSS entries as a baseline. Timestamp of discovery is not date of publication.
* [`journal-watch/public/discoveries.json`](journal-watch/public/discoveries.json): recent observations, additions from latest run, per-feed status and cumulative counts. For the ChatGPT weekly brief, this is the main feed-history discovery index; use `history.json` for older items and prior deduplication.
* [`journal-watch/public/latest_compact.json`](journal-watch/public/latest_compact.json): lightweight snapshot for checking publisher-feed freshness.
* [`journal-watch/public/latest.json`](journal-watch/public/latest.json): full most recent RSS result, including items that might disappear from tomorrow's feed.

The automated regression tests in [`tests/test_history.py`](tests/test_history.py) run before every ingestion.

## Limitations

These eight feeds are **not the complete 14-journal watch**. For six additional journals, and to verify the eight publishers' Online First listings, the weekly ChatGPT task must also consult publisher pages and other public sources. Several sources (for example CJE) have stale RSS items; SCED items are undated. RSS `feed_date` and archive `first_seen_utc` are **not confirmed first-online publication dates**.

The archive contains public article metadata, not paywalled papers, authenticated institutional access, or copyrighted PDFs. GitHub data and workflow logs are public. No subscription credentials are stored here.
