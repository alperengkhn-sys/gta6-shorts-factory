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

    def test_rejects_replay_on_a_different_render_attempt(self):
        with self.assertRaisesRegex(ValueError, "attestation is invalid"):
            verify_permission_attestation(
                secret=self.secret,
                signature=self.signature,
                render_attempt="2",
                now=dt.datetime(2026, 11, 26, tzinfo=dt.timezone.utc),
                **{k: v for k, v in self.fields.items() if k != "render_attempt"},
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
        with self.assertRaisesRegex(ValueError, "45–175"):
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
