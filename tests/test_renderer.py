import unittest
from renderer.render import clean, split_caption, stamp, validate_source_url

class RendererHelpersTest(unittest.TestCase):
    def test_discovery_matches_common_gta_vi_title_spellings(self):
        for title in ("GTA 6 Police Chase", "GTA VI Gameplay", "Grand Theft Auto VI Trailer", "Grand Theft Auto 6 News"):
            with self.subTest(title=title):
                self.assertIsNotNone(GTA6.search(title))
        self.assertIsNone(GTA6.search("Red Dead Redemption 2"))

    def test_channel_id_resolves_to_uploads_playlist(self):
        channel_id = "UC" + "a" * 22
        self.assertEqual(
            channel_uploads_playlist("https://www.youtube.com/channel/" + channel_id + "/videos"),
            "https://www.youtube.com/playlist?list=UU" + "a" * 22,
        )

    def test_handle_resolves_channel_id_from_page_metadata(self):
        channel_id = "UC" + "b" * 22
        html = '<meta itemprop="channelId" content="' + channel_id + '">'
        self.assertEqual(
            channel_uploads_playlist("https://www.youtube.com/@VIRUSHGTA6", html),
            "https://www.youtube.com/playlist?list=UU" + "b" * 22,
        )

    def test_rss_fallback_extracts_public_video_entries(self):
        channel_id = "UC" + "c" * 22
        video_id = "abcdefghijk"
        feed = f'''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015">
          <entry><yt:videoId>{video_id}</yt:videoId><title>GTA VI Gameplay</title>
            <author><name>VIRUSHGTA6</name></author></entry>
        </feed>'''
        entries = channel_rss_entries("https://www.youtube.com/channel/" + channel_id, feed)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["webpage_url"], "https://www.youtube.com/watch?v=" + video_id)
        self.assertEqual(entries[0]["channel"], "VIRUSHGTA6")

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

    def test_accepts_public_https_video_and_clip_urls(self):
        self.assertTrue(validate_source_url("https://example.com/public-clip"))
        self.assertTrue(validate_source_url("https://www.twitch.tv/example/clip/ExampleClip"))
        self.assertTrue(validate_source_url("https://example.com/video.mp4"))
        self.assertFalse(validate_source_url("http://example.com/video.mp4"))
        self.assertFalse(validate_source_url("https://user:pass@example.com/video.mp4"))
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
