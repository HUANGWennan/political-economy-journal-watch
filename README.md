# Political Economy Journal Watch

[中文](#chinese) · [English](#english)

<a name="english"></a>
## English

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

---

<a name="chinese"></a>
## 中文

汇集 8 种英文期刊的 RSS 元数据，并长期保存书目历史。独立运行的 ChatGPT 每周简报共检查 **14 种期刊**。

### 每日采集

[Journal RSS Cloud Snapshot](.github/workflows/journal-rss-cloud.yml) 每天 UTC 07:17 运行；解析器、工作流或测试变化时也会触发。不需要 Mac、设备登录或付费 API。

- [`rss_parser.py`](journal-watch/rss_parser.py) 解析 RSS 2.0、Atom 和 RDF/RSS 1.0，并报告订阅源错误和过时日期。
- [`history.py`](journal-watch/history.py) 按 DOI、规范链接或同刊标题去重，将新记录加入历史；订阅源轮换或失效不会删除旧记录。
- [`history.json`](journal-watch/public/history.json) 是累积书目存档，记录首次和最近观察时间。初次运行导入当时的全部订阅条目作为基线。
- [`discoveries.json`](journal-watch/public/discoveries.json) 是每周简报的近期发现索引，含本轮新增、各源状态和累计数。查旧文章和去重用历史文件。
- [`latest_compact.json`](journal-watch/public/latest_compact.json) 是用于查看新鲜度的轻量快照；[`latest.json`](journal-watch/public/latest.json) 含最近一轮完整结果。

采集前运行 [历史合并回归测试](tests/test_history.py)。

### 限制

RSS 不是完整的 14 刊覆盖。另 6 刊以及 8 刊的 Online First 状态仍须查出版商页面和其他公开来源。CJE 等可能有陈旧条目，SCED 有不带日期的条目；RSS 日期和首次发现时间都不是经确认的在线发表日。仓库和日志公开，仅存公开元数据，不存订阅凭据或论文 PDF。
