import os
import sys
import tempfile
import unittest
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "renderer"))
import render


class RendererPolicyTests(unittest.TestCase):
    def setUp(self):
        os.environ.pop("RENDER_TEST_MODE", None)
        os.environ["OFFLINE_MIN_SCORE"] = "68"

    def test_voiceover_generator_is_removed(self):
        self.assertFalse(hasattr(render, "create_voiceover"))

    def test_renderer_has_no_subtitle_filter_parameter(self):
        self.assertNotIn("subtitles_path", render.video_filter.__code__.co_varnames)
        graph, _ = render.video_filter(45, [])
        self.assertNotIn("subtitles=", graph)

    def test_low_visual_activity_is_rejected(self):
        metrics = {
            "scene_change_count": 2, "silence_ratio": 0.1, "mean_volume_db": -20,
            "frame_motion_mean": 0.2, "active_motion_ratio": 0.05, "max_static_seconds": 12.0
        }
        with tempfile.TemporaryDirectory() as work:
            with self.assertRaisesRegex(RuntimeError, "actual gameplay movement"):
                render.vision_review("unused.mp4", Path(work), metrics, "GTA VI")

    def test_long_silence_is_softened_when_gameplay_motion_is_usable(self):
        metrics = {
            "scene_change_count": 8, "silence_ratio": 0.7, "mean_volume_db": -20,
            "frame_motion_mean": 3.4, "active_motion_ratio": 0.55, "max_static_seconds": 2.0
        }
        with tempfile.TemporaryDirectory() as work:
            review = render.vision_review("unused.mp4", Path(work), metrics, "GTA 6 explosive gameplay action")
        self.assertTrue(review["status"] == "passed")
        self.assertTrue(any("quiet portions detected" in reason for reason in review["reasons"]))

    def test_static_loading_screen_is_rejected(self):
        metrics = {
            "scene_change_count": 8, "silence_ratio": 0.1, "mean_volume_db": -20,
            "frame_motion_mean": 0.0, "active_motion_ratio": 0.0, "max_static_seconds": 30.0
        }
        with tempfile.TemporaryDirectory() as work:
            with self.assertRaisesRegex(RuntimeError, "actual gameplay movement"):
                render.vision_review("unused.mp4", Path(work), metrics, "GTA VI")

    def test_long_static_broadcast_segment_is_softened_when_overall_motion_is_good(self):
        metrics = {
            "scene_change_count": 8, "silence_ratio": 0.1, "mean_volume_db": -20,
            "frame_motion_mean": 3.2, "active_motion_ratio": 0.55, "max_static_seconds": 9.0
        }
        with tempfile.TemporaryDirectory() as work:
            review = render.vision_review("unused.mp4", Path(work), metrics, "GTA 6 gameplay police chase")
        self.assertEqual(review["status"], "passed")
        self.assertTrue(any("retained because overall gameplay movement" in reason for reason in review["reasons"]))

    def test_frame_motion_summary_distinguishes_active_gameplay(self):
        summary = render.summarize_frame_motion([0.0, 0.0, 4.0, 5.0, 3.5, 4.2, 0.0, 3.0], 4.0)
        self.assertGreaterEqual(summary["active_motion_ratio"], 0.5)
        self.assertEqual(summary["max_static_seconds"], 1.0)

    def test_source_shorter_than_45_seconds_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "45 seconds"):
            render.validate_source_quality(44.9, {"width": 1920, "height": 1080, "fps": 60})

    def test_source_below_720p_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "720p"):
            render.validate_source_quality(50, {"width": 1280, "height": 540, "fps": 60})

    def test_source_below_30fps_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "30 fps"):
            render.validate_source_quality(50, {"width": 1920, "height": 1080, "fps": 25})

    def test_hd_80_second_source_passes(self):
        result = render.validate_source_quality(80, {"width": 1920, "height": 1080, "fps": 60})
        self.assertTrue(result["source_quality_passed"])

    def test_original_brand_sting_is_exactly_four_seconds(self):
        with tempfile.TemporaryDirectory() as work:
            audio_path = render.create_brand_sting(Path(work), duration=4.0)
            with wave.open(str(audio_path), "rb") as audio:
                self.assertEqual(audio.getnframes() / audio.getframerate(), 4.0)
                self.assertEqual(audio.getnchannels(), 2)


if __name__ == "__main__":
    unittest.main()
