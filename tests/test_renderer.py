import os
import unittest
from unittest.mock import patch

from renderer.render import (
    build_twitch_download_command,
    check_audio_coverage,
    clean,
    split_caption,
    stamp,
    validate_source_url,
    vision_review,
)


class RendererHelpersTest(unittest.TestCase):

    def test_twitch_download_uses_ffmpeg_for_hls_and_expanded_probe(self):
        command = build_twitch_download_command(
            "https://www.twitch.tv/example/clip/ExampleClip", "/tmp/source.mp4"
        )
        self.assertIn("--downloader", command)
        self.assertEqual(command[command.index("--downloader") + 1], "m3u8:ffmpeg")
        self.assertIn("-analyzeduration 20000000 -probesize 50000000",
                      command[command.index("--downloader-args") + 1])

    def test_audio_coverage_rejects_truncated_source_before_render(self):
        fake_probe = json.dumps({
            "format": {"duration": "30.0"},
            "streams": [
                {"codec_type": "video", "duration": "30.0"},
                {"codec_type": "audio", "duration": "8.9"},
            ],
        })
        with patch("renderer.render.run", return_value=fake_probe):
            with self.assertRaisesRegex(RuntimeError, "audio track is truncated"):
                check_audio_coverage("/tmp/source.mp4", "Test clip")

    def test_audio_coverage_accepts_full_length_source(self):
        fake_probe = json.dumps({
            "format": {"duration": "30.0"},
            "streams": [
                {"codec_type": "video", "duration": "30.0"},
                {"codec_type": "audio", "duration": "29.8"},
            ],
        })
        with patch("renderer.render.run", return_value=fake_probe):
            info = check_audio_coverage("/tmp/source.mp4", "Test clip")
        self.assertEqual(info["format"]["duration"], "30.0")

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
        self.assertEqual(trailing_silence_seconds("[silencedetect] silence_start: 8.0", 55.0), 47.0)

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

    def test_offline_review_scores_using_local_media_metadata(self):
        metrics = {
            "scene_change_count": 14,
            "silence_ratio": 0.03,
            "mean_volume_db": -22.0,
        }
        with patch.dict(os.environ, {"OFFLINE_MIN_SCORE": "60"}, clear=False):
            review = vision_review(None, None, metrics=metrics, title="GTA 6 explosive police chase")
        self.assertGreaterEqual(review["score"], 60)
        self.assertEqual(review["provider"], "local_rules")
        self.assertEqual(review["frames_sampled"], 0)
        self.assertTrue(any("no paid AI service" in reason for reason in review["reasons"]))

    def test_offline_review_rejects_low_activity_clip(self):
        metrics = {
            "scene_change_count": 0,
            "silence_ratio": 0.5,
            "mean_volume_db": -42.0,
        }
        with patch.dict(os.environ, {"OFFLINE_MIN_SCORE": "60"}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "Offline quality rules rejected"):
                vision_review(None, None, metrics=metrics, title="GTA 6 loading screen")


if __name__ == "__main__":
    unittest.main()
