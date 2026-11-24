import unittest
from unittest.mock import patch
from renderer.render import clean, split_caption, stamp, validate_source_url, tts_executable

class RendererHelpersTest(unittest.TestCase):
    def test_clean_collapses_whitespace(self):
        self.assertEqual(clean("  GTA6\n  moment  "), "GTA6 moment")

    def test_split_caption_keeps_all_words(self):
        text = "This is a short test for readable captions across multiple lines"
        chunks = split_caption(text, limit=18)
        self.assertTrue(chunks)
        flattened = " ".join(chunks).replace("\n", " ")
        self.assertEqual(flattened, text)
        self.assertTrue(all(len(line) <= 18 for chunk in chunks for line in chunk.split("\n")))

    def test_stamp_formats_subseconds(self):
        self.assertEqual(stamp(1.234), "00:00:01,234")

    def test_stamp_formats_hours(self):
        self.assertEqual(stamp(3661.005), "01:01:01,005")

    def test_tts_prefers_espeak_ng_and_falls_back_to_espeak(self):
        with patch("renderer.render.shutil.which", side_effect=lambda name: "/usr/bin/espeak-ng" if name == "espeak-ng" else "/usr/bin/espeak"):
            self.assertEqual(tts_executable(), "/usr/bin/espeak-ng")
        with patch("renderer.render.shutil.which", side_effect=lambda name: "/usr/bin/espeak" if name == "espeak" else None):
            self.assertEqual(tts_executable(), "/usr/bin/espeak")

    def test_accepts_public_https_video_and_clip_urls(self):
        self.assertTrue(validate_source_url("https://clips.twitch.tv/SomeClip"))
        self.assertTrue(validate_source_url("https://www.youtube.com/watch?v=example"))
        self.assertTrue(validate_source_url("https://example.com/video.mp4"))
        self.assertFalse(validate_source_url("http://example.com/video.mp4"))
        self.assertFalse(validate_source_url("https://twitch.tv.example.com/clip"))
        self.assertFalse(validate_source_url("https://user:pass@example.com/video.mp4"))
        self.assertFalse(validate_source_url("file:///etc/passwd"))

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
