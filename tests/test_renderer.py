import unittest
from renderer.render import clean, split_caption, stamp, validate_source_url

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

    def test_accepts_https_twitch_clip_urls(self):
        self.assertTrue(validate_source_url("https://clips.twitch.tv/SomeClip"))
        self.assertTrue(validate_source_url("https://www.twitch.tv/creator/clip/SomeClip"))

    def test_rejects_non_twitch_and_unsafe_urls(self):
        for url in (
            "http://clips.twitch.tv/SomeClip",
            "https://example.com/video.mp4",
            "https://twitch.tv.example.com/clip",
            "https://user:pass@twitch.tv/clip",
            "file:///etc/passwd",
        ):
            with self.subTest(url=url):
                self.assertFalse(validate_source_url(url))

if __name__ == "__main__":
    unittest.main()
