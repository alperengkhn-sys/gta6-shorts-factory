import json
import os
import unittest
from unittest.mock import patch

from renderer.render import (
    auto_trim_silence,
    build_twitch_download_command,
    download_direct_twitch_mp4,
    check_audio_coverage,
    clean,
    split_caption,
    stamp,
    validate_source_url,
    video_filter,
    vision_review,
)
from renderer.visual_quality import compare_content_fingerprints, is_blurry, has_persistent_facecam


class RendererHelpersTest(unittest.TestCase):

    def test_twitch_download_uses_ffmpeg_for_hls_and_expanded_probe(self):
        command = build_twitch_download_command(
            "https://www.twitch.tv/example/clip/ExampleClip", "/tmp/source.mp4"
        )
        self.assertIn("--downloader", command)
        self.assertEqual(command[command.index("--downloader") + 1], "m3u8:ffmpeg")
        self.assertIn("-analyzeduration 20000000 -probesize 50000000",
                      command[command.index("--downloader-args") + 1])

    def test_production_download_uses_signed_twitch_api_mp4_url(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch

        class FakeResponse:
            headers = {"Content-Type": "video/mp4", "Content-Length": "9"}
            def __init__(self):
                self.data = b"fake-mp4"
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def geturl(self):
                return "https://clips-media-assets2.twitch.tv/test-download.mp4?sig=test"
            def read(self, size=-1):
                if not self.data:
                    return b""
                chunk, self.data = self.data[:size], self.data[size:]
                return chunk

        with TemporaryDirectory() as directory:
            target = Path(directory) / "source.mp4"
            with patch("renderer.render.urllib.request.urlopen", return_value=FakeResponse()) as urlopen:
                size = download_direct_twitch_mp4(
                    "https://clips-media-assets2.twitch.tv/test-download.mp4?sig=test",
                    target,
                )
        self.assertEqual(size, 8)
        self.assertEqual(target.read_bytes(), b"fake-mp4")
        self.assertEqual(urlopen.call_count, 1)

    def test_production_download_rejects_twitch_page_url_and_non_https(self):
        from unittest.mock import patch
        with patch("renderer.render.urllib.request.urlopen") as urlopen:
            with self.assertRaisesRegex(RuntimeError, "not a direct MP4"):
                download_direct_twitch_mp4(
                    "https://www.twitch.tv/tester/clip/TestClip", "/tmp/should-not-download.mp4"
                )
            with self.assertRaisesRegex(RuntimeError, "secure direct Twitch"):
                download_direct_twitch_mp4("http://cdn.example/test.mp4", "/tmp/should-not-download.mp4")
        urlopen.assert_not_called()

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

    def test_highlight_selection_preserves_80_second_source(self):
        from renderer.render import select_highlight_window
        self.assertEqual(select_highlight_window(80, [], [10, 20]), (0.0, 80.0, 0.0))

    def test_silence_trim_preserves_45_second_target(self):
        from pathlib import Path
        silence_log = "[silencedetect] silence_start: 5.0\\n[silencedetect] silence_end: 16.0 | silence_duration: 11.0"
        probe = json.dumps({"format": {"duration": "55.0"}})
        source = Path("/tmp/source-55.mp4")
        with patch("renderer.render.run", side_effect=[silence_log, probe]):
            result, duration, removed = auto_trim_silence(source, Path("/tmp"), minimum_remaining=45)
        self.assertEqual(result, source)
        self.assertEqual(duration, 55.0)
        self.assertEqual(removed, 0)

    def test_silence_trim_never_reduces_valid_short_below_25_seconds(self):
        from pathlib import Path
        silence_log = "[silencedetect] silence_start: 4.0\\n[silencedetect] silence_end: 9.2 | silence_duration: 5.2"
        probe = json.dumps({"format": {"duration": "30.0"}})
        source = Path("/tmp/source-30.mp4")
        with patch("renderer.render.run", side_effect=[silence_log, probe]):
            result, duration, removed = auto_trim_silence(source, Path("/tmp"), minimum_remaining=25)
        self.assertEqual(result, source)
        self.assertEqual(duration, 30.0)
        self.assertEqual(removed, 0)

    def test_video_filter_adds_like_subscribe_notification_cta_on_last_five_seconds(self):
        from pathlib import Path
        assets = [(Path("subscribe.png"), "390:-1", "0", "0", "ending")]
        filter_graph, _ = video_filter(50, assets)
        self.assertIn("LIKE  •  SUBSCRIBE  •  TURN ON NOTIFICATIONS", filter_graph)
        self.assertIn("between(t,45.000,50.000)", filter_graph)

    def test_rejects_local_and_private_network_hosts(self):
        for url in (
            "https://localhost/video.mp4",
            "https://127.0.0.1/video.mp4",
            "https://192.168.1.20/video.mp4",
            "https://router.local/video.mp4",
        ):
            with self.subTest(url=url):
                self.assertFalse(validate_source_url(url))

    def test_content_fingerprint_detects_same_gameplay_across_different_sources(self):
        import random
        rng = random.Random(831)
        shared = [f"{rng.getrandbits(64):016x}" for _ in range(30)]
        first = {"frame_hashes": shared + [f"{rng.getrandbits(64):016x}" for _ in range(10)]}
        second = {"frame_hashes": shared[5:] + [f"{rng.getrandbits(64):016x}" for _ in range(5)]}
        result = compare_content_fingerprints(first, second)
        self.assertTrue(result["duplicate"])
        self.assertGreaterEqual(result["coverage"], 0.65)

    def test_content_fingerprint_does_not_flag_unrelated_videos(self):
        import random
        rng_a, rng_b = random.Random(1), random.Random(2)
        first = {"frame_hashes": [f"{rng_a.getrandbits(64):016x}" for _ in range(40)]}
        second = {"frame_hashes": [f"{rng_b.getrandbits(64):016x}" for _ in range(40)]}
        self.assertFalse(compare_content_fingerprints(first, second)["duplicate"])

    def test_blur_gate_rejects_only_heavily_blurred_content(self):
        self.assertTrue(is_blurry([2, 3, 5, 4, 6, 3]))
        self.assertFalse(is_blurry([120, 100, 90, 130, 80, 110]))

    def test_facecam_gate_requires_persistent_face_in_same_region(self):
        detected, corner, hits, required = has_persistent_facecam(
            {"top_right": 5, "bottom_left": 1}, 10
        )
        self.assertTrue(detected)
        self.assertEqual(corner, "top_right")
        self.assertEqual(hits, 5)
        self.assertEqual(required, 4)
        self.assertFalse(has_persistent_facecam({"top_right": 2}, 10)[0])

    def test_offline_review_scores_using_local_media_metadata(self):
        metrics = {
            "scene_change_count": 14,
            "silence_ratio": 0.03,
            "mean_volume_db": -22.0,
            "frame_motion_mean": 4.2,
            "active_motion_ratio": 0.72,
            "max_static_seconds": 1.0,
        }
        with patch.dict(os.environ, {"OFFLINE_MIN_SCORE": "60"}, clear=False):
            review = vision_review(None, None, metrics=metrics, title="GTA 6 explosive police chase")
        self.assertGreaterEqual(review["score"], 60)
        self.assertEqual(review["provider"], "local_rules")
        self.assertEqual(review["frames_sampled"], 0)
        self.assertTrue(any("no paid AI service" in reason for reason in review["reasons"]))

    def test_offline_review_accepts_continuous_gameplay_without_scene_cuts(self):
        metrics = {
            "scene_change_count": 0,
            "silence_ratio": 0.03,
            "mean_volume_db": -22.0,
            "frame_motion_mean": 4.2,
            "active_motion_ratio": 0.72,
            "max_static_seconds": 1.0,
        }
        with patch.dict(os.environ, {"OFFLINE_MIN_SCORE": "68"}, clear=False):
            review = vision_review(None, None, metrics=metrics, title="GTA 6 continuous gameplay drive")
        self.assertGreaterEqual(review["score"], 68)
        self.assertTrue(any("Continuous gameplay scene" in reason for reason in review["reasons"]))

    def test_offline_review_keeps_clip_with_long_static_pause_if_overall_motion_is_good(self):
        metrics = {
            "scene_change_count": 2,
            "silence_ratio": 0.08,
            "mean_volume_db": -22.0,
            "frame_motion_mean": 3.2,
            "active_motion_ratio": 0.55,
            "max_static_seconds": 9.0,
        }
        with patch.dict(os.environ, {"OFFLINE_MIN_SCORE": "68"}, clear=False):
            review = vision_review(None, None, metrics=metrics, title="GTA 6 gameplay police chase")
        self.assertGreaterEqual(review["score"], 68)
        self.assertTrue(any("retained because overall gameplay movement" in reason for reason in review["reasons"]))

    def test_offline_review_keeps_high_silence_ratio_if_footage_and_audio_are_usable(self):
        metrics = {
            "scene_change_count": 8,
            "silence_ratio": 0.70,
            "mean_volume_db": -20.0,
            "frame_motion_mean": 3.4,
            "active_motion_ratio": 0.55,
            "max_static_seconds": 2.0,
        }
        with patch.dict(os.environ, {"OFFLINE_MIN_SCORE": "60"}, clear=False):
            review = vision_review(None, None, metrics=metrics, title="GTA 6 explosive gameplay action")
        self.assertGreaterEqual(review["score"], 60)
        self.assertTrue(any("quiet portions detected" in reason for reason in review["reasons"]))

    def test_offline_review_rejects_low_activity_clip(self):
        metrics = {
            "scene_change_count": 5,
            "silence_ratio": 0.5,
            "mean_volume_db": -20.0,
            "frame_motion_mean": 3.0,
            "active_motion_ratio": 0.10,
            "max_static_seconds": 8.0,
        }
        with patch.dict(os.environ, {"OFFLINE_MIN_SCORE": "60"}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "too little actual gameplay movement"):
                vision_review(None, None, metrics=metrics, title="GTA 6 loading screen")


    def test_shorts_thumbnail_upload_works_with_youtube_upload_scope_only(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from renderer.youtube_upload import upload_custom_thumbnail
        upload_scope = "https://www.googleapis.com/auth/youtube.upload"
        with TemporaryDirectory() as directory:
            cover = Path(directory) / "cover.jpg"
            cover.write_bytes(b"jpeg-test")
            with patch("renderer.youtube_upload.request", return_value=(200, {}, b"{}")) as api, \
                 patch("renderer.youtube_upload.time.sleep") as sleep:
                result = upload_custom_thumbnail("video123", cover, "access-token", {upload_scope})
        self.assertEqual(result, "uploaded")
        sleep.assert_called_once_with(120)
        self.assertEqual(api.call_count, 1)
        self.assertIn("/thumbnails/set?videoId=video123", api.call_args.args[0])
        self.assertEqual(api.call_args.args[1], b"jpeg-test")
        self.assertEqual(api.call_args.args[3], "POST")

    def test_shorts_thumbnail_waits_for_processing_when_read_scope_exists(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from renderer.youtube_upload import upload_custom_thumbnail
        read_scope = "https://www.googleapis.com/auth/youtube.readonly"
        upload_scope = "https://www.googleapis.com/auth/youtube.upload"
        status = json.dumps({"items": [{
            "status": {"uploadStatus": "processed"},
            "processingDetails": {"processingStatus": "succeeded"},
        }]}).encode()
        with TemporaryDirectory() as directory:
            cover = Path(directory) / "cover.jpg"
            cover.write_bytes(b"jpeg-test")
            with patch("renderer.youtube_upload.request", side_effect=[
                (200, {}, status), (200, {}, b"{}")
            ]) as api, patch("renderer.youtube_upload.time.sleep") as sleep:
                result = upload_custom_thumbnail("video123", cover, "access-token", {read_scope, upload_scope})
        self.assertEqual(result, "uploaded")
        self.assertEqual(api.call_count, 2)
        self.assertIn("/videos?part=processingDetails,status&id=video123", api.call_args_list[0].args[0])
        self.assertIn("/thumbnails/set?videoId=video123", api.call_args_list[1].args[0])
        sleep.assert_not_called()

    def test_shorts_thumbnail_does_not_upload_before_processing_when_read_scope_times_out(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from renderer.youtube_upload import upload_custom_thumbnail
        read_scope = "https://www.googleapis.com/auth/youtube.readonly"
        upload_scope = "https://www.googleapis.com/auth/youtube.upload"
        status = json.dumps({"items": [{
            "status": {"uploadStatus": "uploaded"},
            "processingDetails": {"processingStatus": "processing"},
        }]}).encode()
        with TemporaryDirectory() as directory:
            cover = Path(directory) / "cover.jpg"
            cover.write_bytes(b"jpeg-test")
            with patch("renderer.youtube_upload.request", return_value=(200, {}, status)) as api, \
                 patch("renderer.youtube_upload.time.sleep") as sleep:
                result = upload_custom_thumbnail("video123", cover, "access-token", {read_scope, upload_scope})
        self.assertEqual(result, "processing_timeout")
        self.assertEqual(api.call_count, 40)
        self.assertEqual(sleep.call_count, 40)

    def test_shorts_thumbnail_rejects_unrelated_oauth_scope(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from renderer.youtube_upload import upload_custom_thumbnail
        with TemporaryDirectory() as directory:
            cover = Path(directory) / "cover.jpg"
            cover.write_bytes(b"jpeg-test")
            with patch("renderer.youtube_upload.request") as api, \
                 patch("renderer.youtube_upload.time.sleep") as sleep:
                result = upload_custom_thumbnail("video123", cover, "access-token", {"openid"})
        self.assertEqual(result, "missing_thumbnail_upload_scope")
        api.assert_not_called()
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
