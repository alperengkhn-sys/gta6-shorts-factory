# Implementation

The production path is Twitch public clip discovery → yt-dlp media retrieval → vertical MP4 rendering → English YouTube metadata → public YouTube upload.

- Twitch Helix app credentials are used only for discovery and clip metadata. No personal Twitch OAuth or broadcaster editor permission is part of the public clip download path.
- The renderer downloads the public Twitch clip URL with yt-dlp, analyzes audio activity and scene changes, trims long silences, preserves original audio, and outputs a 1080x1920 MP4.
- Branding overlays, a cover image, English editorial TXT, and a combined ZIP are produced for each render.
- `renderer/youtube_upload.py` uploads with `privacyStatus=public`, uploads the cover, and returns the public video URL.
- Missing YouTube OAuth secrets are a visible upload failure, not a successful skipped upload.
- Worker scheduled trigger runs every three hours and automatically discovers, prepares and dispatches queued Shorts.
- The dashboard provides a one-link Twitch clip intake and shows render, ZIP and YouTube publication results.
- No livestream broadcasting, PostMassive integration, or YouTube source discovery exists.
- Existing D1 source rows are preserved; schema changes are additive.
