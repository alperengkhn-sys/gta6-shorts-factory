# Cloud rendering

## Automatic dashboard flow

1. Configure `GITHUB_TOKEN` (Actions: write access to this repository) and `RENDER_WEBHOOK_SECRET` in the Cloudflare Worker settings.
2. Add the same `RENDER_WEBHOOK_SECRET` value to GitHub Actions repository secrets.
3. Open the dashboard. Either add a public HTTPS video/clip URL manually or enter a public channel, videos-tab, or playlist URL in the discovery panel. Discovery scans recent entries and keeps GTA VI-titled videos.
4. Confirm the source or channel reuse-rights checkbox only when you own the content or have the necessary license / explicit permission for editing and commercial YouTube use. The checkbox is an operator attestation, not legal proof or a copyright clearance service.
5. Create the editorial package and start MP4 rendering. Clips shorter than 25 seconds are rejected. Clips of 45 seconds or longer are preferred in discovery scoring and are kept at 45 seconds or more after silence trimming; 25–44 second clips remain a fallback when longer sources are unavailable. Sources longer than 55 seconds are reduced to a candidate 55-second window using non-silent audio and scene-change density. This heuristic cannot understand the story or guarantee that the selected segment is the best moment.
6. The workflow renders 1080×1920 H.264/AAC, preserves source audio, adds generated English narration and synchronized captions when an editorial script is available, applies the persistent VI RUSH logo, uses the supplied artwork as the opening bumper and closing card, and displays the supplied subscribe and notification images plus a like/subscribe/bell text reminder during the final five seconds. The images are layered so the closing card does not cover the CTA graphics.
7. Each Short receives a source-topic title, an English description with creator credit and source link, a category-specific and source-topic tag set, relevant hashtags, and a title-stamped cover. The MP4, editorial TXT, cover JPG, media analysis and branding files are delivered in a combined ZIP. GitHub Release links provide direct MP4 and ZIP downloads when release publishing succeeds; a seven-day Actions artifact is also stored and render status is posted back to the Worker.

## YouTube publishing

Create a Google Cloud project, enable **YouTube Data API v3**, and create OAuth credentials with the `https://www.googleapis.com/auth/youtube.upload` scope. Add `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, and `YOUTUBE_REFRESH_TOKEN` as GitHub Actions secrets. When all three are configured, successful renders upload **publicly**. The uploader waits briefly for processing before applying the custom cover; custom thumbnail setting still depends on channel eligibility and the API's permissions. If the secrets are absent, upload is reported as `not_configured`.

## Manual fallback

1. Open the repository's **Actions** tab.
2. Select **Render GTA6 Short** → **Run workflow**.
3. Enter a public HTTPS source URL supported by yt-dlp and a title.
4. Use this fallback only after independently confirming that you have the necessary rights. The manual workflow does not replace the dashboard's rights-attestation record.

## Limits and safeguards

- Rendering runs in GitHub Actions; it does not use the local PC for processing.
- GitHub Actions usage is quota-limited; daily output volume is not guaranteed.
- The MP4 preserves source audio, adds the original VI RUSH sonic sting, and uses generated voiceover/captions when the editorial script is long enough.
- The free editorial script and SEO are generated from the Twitch source title, creator and category. They are not a frame-by-frame understanding of the clip; verify factual claims against the footage.
- Public accessibility is not permission to reuse a video. The system cannot determine copyright ownership, fair use, or platform licensing. Do not publish content without the necessary rights.
- Artifact retention is seven days. Release links are subject to repository release permissions.

## Channel branding and per-video cover

- `branding/logo.png` is applied as a persistent watermark.
- `renderer/prepare_branding.py` removes checkerboard backgrounds from the subscribe and notification JPGs.
- The VI RUSH artwork is used for the intro and outro; subscribe and bell overlays, plus the like/subscribe/notification reminder, appear over the final card during the final five seconds.
- Every rendered Short receives a separate `short-cover.jpg` generated from actual footage with the title. YouTube custom thumbnail upload is attempted after upload.
