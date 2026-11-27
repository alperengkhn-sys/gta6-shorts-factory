import json
import tempfile
import unittest
from pathlib import Path

from renderer.youtube_analytics import build_video_report_params, published_shorts


class YouTubeAnalyticsTests(unittest.TestCase):
    def test_video_report_requires_known_short_ids(self):
        common = {
            "ids": "channel==MINE",
            "startDate": "2026-11-01",
            "endDate": "2026-11-27",
            "metrics": "views,likes",
        }
        self.assertIsNone(build_video_report_params(common, []))
        params = build_video_report_params(common, ["abc123", "def456"])
        self.assertEqual(params["dimensions"], "video")
        self.assertEqual(params["filters"], "video==abc123,def456")
        self.assertEqual(params["maxResults"], "200")

    def test_marker_loader_extracts_watch_and_shorts_urls(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one.json").write_text(json.dumps({
                "video_url": "https://www.youtube.com/watch?v=videoOne",
                "title": "Police chase",
            }), encoding="utf-8")
            (root / "two.json").write_text(json.dumps({
                "video_url": "https://www.youtube.com/shorts/videoTwo",
                "title": "Wild escape",
            }), encoding="utf-8")
            result = published_shorts(root)
        self.assertEqual(result, {"videoOne": "Police chase", "videoTwo": "Wild escape"})


if __name__ == "__main__":
    unittest.main()
