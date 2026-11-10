"""Offline history regression tests, run before cloud RSS fetch."""
import datetime as dt
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "journal-watch"))
from history import update_history


def item(title, doi=None, link=None):
    return {
        "title": title, "doi": doi, "link": link or "https://example.org/article/" + title.replace(" ", "-"),
        "feed_date": "2026-11-09T00:00:00Z",
        "identifier": "", "summary_excerpt": "abstract",
    }


def snapshot(entries, status="ok"):
    return {"feeds": [{"journal": "Test Journal", "status": status, "items": entries}]}


class HistoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = pathlib.Path(self.temp.name)
        self.history = root / "history.json"
        self.discoveries = root / "discoveries.json"
        self.first = dt.datetime(2026, 11, 9, tzinfo=dt.timezone.utc)
        self.next = self.first + dt.timedelta(days=1)

    def merge(self, entries, when=None, status="ok"):
        return update_history(snapshot(entries, status), when or self.first,
                              self.history, self.discoveries)

    def test_first_run_creates_cumulative_history(self):
        out = self.merge([item("Article A"), item("Article B")])
        self.assertEqual(out["total_historical_articles"], 2)
        self.assertEqual(out["new_this_run"], 2)
        self.assertTrue(self.history.exists())

    def test_repeated_run_preserves_first_seen_and_count(self):
        a = item("Article A")
        first = self.merge([a])
        second = self.merge([a], self.next)
        self.assertEqual(second["new_this_run"], 0)
        self.assertEqual(second["total_historical_articles"], 1)
        self.assertEqual(first["recent_discoveries"][0]["first_seen_utc"],
                         second["recent_discoveries"][0]["first_seen_utc"])

    def test_disappearing_feed_items_are_never_deleted(self):
        self.merge([item("Article A"), item("Article B")])
        after = self.merge([item("Article B"), item("Article C")], self.next)
        self.assertEqual(after["new_this_run"], 1)
        self.assertEqual(after["total_historical_articles"], 3)

    def test_failed_feed_does_not_reset_archive(self):
        self.merge([item("Article A")])
        after = self.merge([], self.next, status="cached_after_error")
        self.assertEqual(after["total_historical_articles"], 1)
        self.assertEqual(after["new_this_run"], 0)

    def test_doi_enrichment_does_not_create_duplicate(self):
        original = item("Article A", link="https://example.org/a")
        enriched = item("Article A", doi="10.1111/example.123", link="https://example.org/a")
        self.merge([original])
        after = self.merge([enriched], self.next)
        self.assertEqual(after["total_historical_articles"], 1)
        self.assertEqual(after["new_this_run"], 0)

    def test_distinct_dois_cannot_merge_by_same_title(self):
        first = item("Introduction", doi="10.1111/example.111")
        second = item("Introduction", doi="10.1111/example.222",
                      link="https://example.org/other")
        after = self.merge([first, second])
        self.assertEqual(after["total_historical_articles"], 2)

    def test_article_after_temporary_feed_error_is_preserved(self):
        self.merge([item("Article A")])
        self.merge([], self.next, status="error")
        recovered = self.merge([item("Article A"), item("Article B")],
                               self.next + dt.timedelta(days=1))
        self.assertEqual(recovered["new_this_run"], 1)
        self.assertEqual(recovered["total_historical_articles"], 2)

    def test_broken_history_refuses_to_reinitialize(self):
        self.history.write_text("invalid-json", encoding="utf8")
        with self.assertRaises(ValueError):
            self.merge([item("Article A")])
        self.assertEqual(self.history.read_text(encoding="utf8"), "invalid-json")


if __name__ == "__main__":
    unittest.main()
