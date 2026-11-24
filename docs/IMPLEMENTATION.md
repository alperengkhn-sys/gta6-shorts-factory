# Production implementation status

## Active pipeline

- Cloudflare Worker discovers public Twitch clips using Twitch Helix.
- Only clips with Twitch's verified Grand Theft Auto VI game category are eligible.
- The system does not request a permission URL or per-clip written approval. Twitch access/category verification is not a copyright license; the channel operator remains responsible for reuse rights.
- Editorial packages are generated from clip title/metadata. They include a hook, original commentary draft, captions, editing notes, SEO description, tags and hashtags.
- Cloudflare Cron runs every three hours and dispatches one highest-scoring eligible render job per cycle (up to eight attempts per day when eligible clips and compute quota are available).
- GitHub Actions downloads the Twitch clip, analyzes media, trims long silent gaps, renders 1080x1920 H.264/AAC, applies the channel logo, creates a unique cover from the actual clip frame, and creates MP4/TXT/cover/branding ZIP delivery files.
- AI narration is synthesized from the editorial script using OpenAI TTS when configured, otherwise edge-tts fallback; original audio is retained and mixed.
- If YouTube OAuth secrets are configured, the uploader creates a private video with a future `publishAt` timestamp 30 minutes after upload. YouTube then auto-publishes it. The scheduler cadence spaces uploads at roughly three-hour intervals.
- Render callbacks record MP4, package, YouTube and thumbnail status in D1.

## Required external configuration

Cloudflare Worker secrets:
- `APP_PASSWORD`
- `TWITCH_CLIENT_ID`
- `TWITCH_CLIENT_SECRET`
- `GITHUB_TOKEN`
- `RENDER_WEBHOOK_SECRET`

GitHub Actions secrets:
- `RENDER_WEBHOOK_SECRET`
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`
- Optional `OPENAI_API_KEY` (edge-tts is the no-key narration fallback)

YouTube OAuth must include `youtube.upload`. Scheduled publishing also depends on the channel's YouTube feature eligibility and successful API authorization. Secret values are never read back or printed.

## Branding assets in the repository

- `branding/logo.png` — channel logo; used as the persistent upper-left video overlay.
- `branding/image_50843161.jpg` — wide VI RUSH / Leonida Loop channel artwork with a subscribe call-to-action; included in the ZIP branding assets.
- `branding/image_2d2a6dba.jpg` — crocodile subscribe graphic; included in the ZIP branding assets.
- `branding/image_c69a04ba.jpg` — notification/bell call-to-action graphic; included in the ZIP branding assets.
- The three JPGs contain a visible checkerboard pattern in the image itself, so they are preserved in the delivery ZIP but are not composited over the footage (that would put the checkerboard on-screen). Transparent overlay versions are needed before using them as timed video overlays.
- A unique per-video cover is generated from a frame of that video's own footage.

## Verification limits

CI passed workflow lint, Worker JavaScript syntax, renderer compilation, unit tests, synthetic end-to-end MP4 rendering, and required deployment-file checks on commit `fa8e20d059db5b7afc1f69f7f6089d7cc8d8d3b1`. The Cloudflare Worker deployment for that revision also succeeded.
CI cannot prove that Twitch currently returns downloadable media, that the channel's OAuth credentials are valid, or that YouTube accepts scheduled publication. A real Twitch-to-YouTube production run remains unverified.

Never reset D1 or delete existing source/draft records.
