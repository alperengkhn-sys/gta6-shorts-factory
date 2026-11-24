import contextlib
import io
import os
import unittest
from unittest.mock import patch

from renderer import youtube_upload


class YouTubeUploadTests(unittest.TestCase):
    def test_missing_oauth_credentials_fail_instead_of_silently_skipping(self):
        env = {
            "YOUTUBE_CLIENT_ID": "",
            "YOUTUBE_CLIENT_SECRET": "",
            "YOUTUBE_REFRESH_TOKEN": "",
        }
        with patch.dict(os.environ, env, clear=False), patch.object(youtube_upload, "output") as output, contextlib.redirect_stderr(io.StringIO()):
            result = youtube_upload.main()
        self.assertEqual(result, 1)
        output.assert_any_call("upload_status", "failed")
        output.assert_any_call("thumbnail_status", "failed")

    def test_public_visibility_is_the_upload_default(self):
        self.assertIn('"privacyStatus": "public"', open(youtube_upload.__file__, encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main()
