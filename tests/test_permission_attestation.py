import datetime as dt
import unittest

from renderer.permission_attestation import (
    make_permission_signature,
    verify_permission_attestation,
)


class PermissionAttestationTests(unittest.TestCase):
    def setUp(self):
        self.secret = "test-only-worker-secret"
        self.fields = {
            "job_id": "job-123",
            "source_url": "https://www.twitch.tv/tester/clip/TestClip",
            "broadcaster_id": "987654321",
            "max_source_seconds": "60",
            "permission_expires_at": "2027-01-01T00:00:00.000Z",
            "render_attempt": "1",
            "download_url": "https://clips-media-assets2.twitch.tv/test-download.mp4?sig=test",
        }
        self.signature = make_permission_signature(self.secret, **self.fields)

    def test_accepts_valid_worker_style_hmac_and_permission_limit(self):
        result = verify_permission_attestation(
            secret=self.secret,
            signature=self.signature,
            now=dt.datetime(2026, 11, 26, tzinfo=dt.timezone.utc),
            **self.fields,
        )
        self.assertTrue(result["verified"])
        self.assertEqual(result["max_source_seconds"], 60.0)
        self.assertEqual(result["broadcaster_id"], "987654321")
        self.assertEqual(result["render_attempt"], "1")

    def test_accepts_creator_authorized_source_limit_above_sixty_seconds(self):
        fields = {**self.fields, "max_source_seconds": "80"}
        signature = make_permission_signature(self.secret, **fields)
        result = verify_permission_attestation(
            secret=self.secret,
            signature=signature,
            now=dt.datetime(2026, 11, 26, tzinfo=dt.timezone.utc),
            **fields,
        )
        self.assertEqual(result["max_source_seconds"], 80.0)

    def test_accepts_public_clip_page_fallback_without_editor_download_url(self):
        fields = {**self.fields, "download_url": "", "permission_expires_at": ""}
        signature = make_permission_signature(self.secret, **fields)
        result = verify_permission_attestation(
            secret=self.secret,
            signature=signature,
            now=dt.datetime(2026, 11, 26, tzinfo=dt.timezone.utc),
            **fields,
        )
        self.assertTrue(result["verified"])
        self.assertEqual(result["download_host"], "public-twitch-page")

    def test_public_fallback_rejects_non_twitch_source_urls(self):
        fields = {**self.fields, "source_url": "https://example.com/not-a-twitch-clip", "download_url": ""}
        signature = make_permission_signature(self.secret, **fields)
        with self.assertRaisesRegex(ValueError, "real public HTTPS Twitch clip"):
            verify_permission_attestation(
                secret=self.secret,
                signature=signature,
                now=dt.datetime(2026, 11, 26, tzinfo=dt.timezone.utc),
                **fields,
            )

    def test_rejects_replay_on_a_different_render_attempt(self):
        with self.assertRaisesRegex(ValueError, "attestation is invalid"):
            verify_permission_attestation(
                secret=self.secret,
                signature=self.signature,
                render_attempt="2",
                now=dt.datetime(2026, 11, 26, tzinfo=dt.timezone.utc),
                **{k: v for k, v in self.fields.items() if k != "render_attempt"},
            )

    def test_rejects_signature_replayed_for_another_direct_download_url(self):
        with self.assertRaisesRegex(ValueError, "attestation is invalid"):
            verify_permission_attestation(
                secret=self.secret,
                signature=self.signature,
                download_url="https://clips-media-assets2.twitch.tv/different.mp4?sig=other",
                now=dt.datetime(2026, 11, 26, tzinfo=dt.timezone.utc),
                **{k: v for k, v in self.fields.items() if k != "download_url"},
            )

    def test_rejects_twitch_clip_page_instead_of_direct_download_url(self):
        invalid = {**self.fields, "download_url": "https://www.twitch.tv/tester/clip/TestClip"}
        signature = make_permission_signature(self.secret, **invalid)
        with self.assertRaisesRegex(ValueError, "not an MP4 URL"):
            verify_permission_attestation(
                secret=self.secret,
                signature=signature,
                now=dt.datetime(2026, 11, 26, tzinfo=dt.timezone.utc),
                **invalid,
            )

    def test_rejects_signature_replayed_for_another_source(self):
        with self.assertRaisesRegex(ValueError, "attestation is invalid"):
            verify_permission_attestation(
                secret=self.secret,
                signature=self.signature,
                source_url="https://www.twitch.tv/another/clip/DifferentClip",
                now=dt.datetime(2026, 11, 26, tzinfo=dt.timezone.utc),
                **{k: v for k, v in self.fields.items() if k != "source_url"},
            )

    def test_rejects_expired_creator_permission(self):
        expired = {
            **self.fields,
            "permission_expires_at": "2026-11-25T00:00:00Z",
        }
        signature = make_permission_signature(self.secret, **expired)
        with self.assertRaisesRegex(ValueError, "has expired"):
            verify_permission_attestation(
                secret=self.secret,
                signature=signature,
                now=dt.datetime(2026, 11, 26, tzinfo=dt.timezone.utc),
                **expired,
            )

    def test_rejects_time_limit_outside_supported_render_range(self):
        invalid = {**self.fields, "max_source_seconds": "180"}
        signature = make_permission_signature(self.secret, **invalid)
        with self.assertRaisesRegex(ValueError, "25–175"):
            verify_permission_attestation(
                secret=self.secret,
                signature=signature,
                now=dt.datetime(2026, 11, 26, tzinfo=dt.timezone.utc),
                **invalid,
            )

    def test_rejects_tampered_source_limit(self):
        with self.assertRaisesRegex(ValueError, "attestation is invalid"):
            verify_permission_attestation(
                secret=self.secret,
                signature=self.signature,
                max_source_seconds="90",
                now=dt.datetime(2026, 11, 26, tzinfo=dt.timezone.utc),
                **{k: v for k, v in self.fields.items() if k != "max_source_seconds"},
            )


if __name__ == "__main__":
    unittest.main()
