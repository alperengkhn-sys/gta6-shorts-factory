import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from renderer.render import clean, request_vision_completion, split_caption, stamp, validate_source_url

class RendererHelpersTest(unittest.TestCase):

    def test_vision_request_retries_transient_rate_limit(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return b'{"choices": []}'

        error = HTTPError("https://api.openai.com", 429, "rate limited",
                          {"Retry-After": "1"}, None)
        with patch("urllib.request.urlopen", side_effect=[error, Response()]) as request:
            with patch("time.sleep") as sleep:
                result = request_vision_completion(object())
        self.assertEqual(result, {"choices": []})
        self.assertEqual(request.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_vision_request_reports_exhausted_quota_without_retry(self):
        body = b'{"error":{"code":"insufficient_quota","message":"You exceeded your quota."}}'
        error = HTTPError("https://api.openai.com", 429, "quota", {}, None)
        error.read = lambda: body
        with patch("urllib.request.urlopen", side_effect=error) as request:
            with patch("time.sleep") as sleep:
                with self.assertRaisesRegex(RuntimeError, "quota/billing is exhausted"):
                    request_vision_completion(object())
        request.assert_called_once()
        sleep.assert_not_called()

    def test_clean_collapses_whitespace(self):
        self.assertEqual(clean("  GTA6\n  moment  "), "GTA6 moment")

    def test_split_caption_keeps_all_words(self):
        text = "This is a short test for readable captions across multiple lines"
        chunks = split_caption(text, limit=18)
        self.assertTrue(chunks)
        flattened = " ".join(chunks).replace("\n", " ")
        self.assertEqual(flattened, text)
        self.assertTrue(all(len(line) <= 18 for chunk in chunks for line in chunk.split("\n")))

    def test_trailing_silence_detects_cut_off_audio(self):
        from renderer.render import trailing_silence_seconds
        log = "[silencedetect] silence_start: 8.0"
        self.assertEqual(trailing_silence_seconds(log, 55.0), 47.0)

    def test_trailing_silence_allows_audio_to_resume(self):
        from renderer.render import trailing_silence_seconds
        log = "[silencedetect] silence_start: 8.0\n[silencedetect] silence_end: 9.0"
        self.assertEqual(trailing_silence_seconds(log, 55.0), 0.0)

    def test_stamp_formats_subseconds(self):
        self.assertEqual(stamp(1.234), "00:00:01,234")

    def test_stamp_formats_hours(self):
        self.assertEqual(stamp(3661.005), "01:01:01,005")

    def test_accepts_only_public_https_twitch_clip_urls(self):
        self.assertTrue(validate_source_url("https://clips.twitch.tv/ExampleClip"))
        self.assertTrue(validate_source_url("https://www.twitch.tv/example/clip/ExampleClip"))
        self.assertTrue(validate_source_url("https://twitch.tv/example/clip/ExampleClip?filter=clips"))
        self.assertFalse(validate_source_url("https://youtube.com/watch?v=example"))
        self.assertFalse(validate_source_url("https://example.com/public-clip"))
        self.assertFalse(validate_source_url("http://www.twitch.tv/example/clip/ExampleClip"))
        self.assertFalse(validate_source_url("https://user:pass@www.twitch.tv/example/clip/ExampleClip"))
        self.assertFalse(validate_source_url("file:///etc/passwd"))


    def test_highlight_selection_prefers_active_scene_dense_window(self):
        from renderer.render import select_highlight_window
        start, length, score = select_highlight_window(
            120, [(0, 40), (80, 120)], [52, 57, 62, 67], window=30, stride=5
        )
        self.assertGreaterEqual(start, 40)
        self.assertLessEqual(start, 55)
        self.assertEqual(length, 30)
        self.assertGreater(score, 30)

    def test_highlight_selection_keeps_short_sources_whole(self):
        from renderer.render import select_highlight_window
        self.assertEqual(select_highlight_window(42, [], [10, 20]), (0.0, 42.0, 0.0))

    def test_rejects_local_and_private_network_hosts(self):
        for url in (
            "https://localhost/video.mp4",
            "https://127.0.0.1/video.mp4",
            "https://192.168.1.20/video.mp4",
            "https://router.local/video.mp4",
        ):
            with self.subTest(url=url):
                self.assertFalse(validate_source_url(url))

if __name__ == "__main__":
    unittest.main()
