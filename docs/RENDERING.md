# Cloud rendering

## Automatic dashboard flow

1. Configure `GITHUB_TOKEN` (Actions: write access to this repository) and `RENDER_WEBHOOK_SECRET` in the Cloudflare Worker settings.
2. Add the same `RENDER_WEBHOOK_SECRET` value to GitHub Actions repository secrets.
3. Open the dashboard. Either add a public HTTPS video/clip URL manually or enter a public channel, videos-tab, or playlist URL in the discovery panel. Discovery scans recent entries and keeps GTA VI-titled videos.
4. Confirm the source or channel reuse-rights checkbox only when you own the content or have the necessary license / explicit permission for editing and commercial YouTube use. The checkbox is an operator attestation, not legal proof or a copyright clearance service.
5. Create the editorial package and start MP4 rendering. For sources longer than 55 seconds, the renderer chooses a candidate 55-second window using non-silent audio and scene-change density, then trims long silent gaps. This heuristic cannot understand the story or guarantee that the selected segment is the best moment; review the result.
6. The workflow renders 1080×1920 H.264/AAC, preserves source audio, applies the supplied channel logo and the converted subscribe/notification overlays during the final five seconds, generates a title-stamped cover from the footage, and creates an MP4, editorial TXT, cover JPG, and combined ZIP. The wide VI RUSH artwork remains in the ZIP.
7. GitHub Release links are used for direct MP4 and ZIP downloads when release publishing succeeds. The workflow also stores a seven-day Actions artifact and posts render status back to the Worker.

## Optional private YouTube upload

Create a Google Cloud project, enable **YouTube Data API v3**, and create OAuth credentials that can grant the scope `https://www.googleapis.com/auth/youtube.upload`. Obtain an offline refresh token for the channel and add these GitHub Actions repository secrets: `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, and `YOUTUBE_REFRESH_TOKEN`. When all three are present, successful renders upload as **private**; the uploader does not schedule public release. Review rights, edits, title, description, and thumbnail, then publish manually. If the secrets are absent, rendering still completes and upload is marked `not_configured`.

## Manual fallback

1. Open the repository's **Actions** tab.
2. Select **Render GTA6 Short** → **Run workflow**.
3. Enter a public HTTPS source URL supported by yt-dlp and a title.
4. Use this fallback only after independently confirming that you have the necessary rights. The manual workflow does not replace the dashboard's rights-attestation record.

## Limits and safeguards

- Rendering runs in GitHub Actions; it does not use the local PC for processing.
- GitHub Actions usage is quota-limited; daily output volume is not guaranteed.
- The built-in English voice is synthetic/basic. Captions are timed across narration, not word-level ASR.
- The editorial script is derived from source metadata and has not independently verified the events in the footage. Review every factual statement.
- Public accessibility is not permission to reuse a video. The system cannot determine copyright ownership, fair use, or platform licensing. Do not publish content without the necessary rights.
- Artifact retention is seven days. Release links are subject to repository release permissions.

## Channel branding and per-video cover

- `branding/logo.png` is applied as a persistent logo overlay.
- `renderer/prepare_branding.py` removes the checkerboard backgrounds from the subscribe and notification JPGs and creates transparent PNG overlays for the final five seconds.
- The wide VI RUSH artwork remains included in the ZIP; it is not currently used as an outro.
- Every rendered Short receives a separate `short-cover.jpg` generated from a frame of the actual footage with the title. YouTube may reject custom thumbnail uploads depending on channel eligibility or image constraints.
