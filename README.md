# GTA6 Shorts Factory

Cloud-first Twitch-to-YouTube Shorts workflow.

## Current baseline

The supplied `GTA6-FACTORY-3.5` Worker is the compatibility baseline. It must be deployed as an in-place upgrade: never drop tables, reset the database, or delete existing source/draft records.

## Existing Cloudflare resources

- Worker: `gta6-shorts-engine`
- D1 database: `gta6-shorts-db`
- D1 binding: `DB`
- Existing secrets: `APP_PASSWORD`, `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`
- Twitch callback: `https://gta6-shorts-engine.alperen-gkhn.workers.dev/auth/twitch/callback`

Never commit secrets, OAuth tokens, cookies, or private clip URLs.

## What 3.5 currently does not do

The baseline creates editorial text packages only. It does not render MP4 files, inspect actual video/audio, or upload to YouTube. Twitch API access is not a grant of copyright or commercial-use permission.

## Upgrade principles

1. Preserve every existing D1 table and record.
2. Use additive migrations only.
3. Keep processing cloud-side.
4. Do not depend on paid APIs or paid SaaS.
5. Never treat Twitch access or category verification as reuse rights; keep rights responsibility explicit and review content before publication.
6. Default YouTube uploads to private until explicitly reviewed.
7. Treat free compute quotas as hard limits; never claim unlimited free rendering.

## Deployment

The repository contains the GTA6-FACTORY-4.1 Worker, Wrangler configuration, and a GitHub Actions cloud renderer with optional channel overlays and per-video cover generation. A three-hour Cloudflare Cron discovers new Twitch clips, verifies the GTA VI game category, prepares editorial packages, and dispatches one render job per run (up to eight attempts per day when sources are available). The Worker can dispatch approved draft jobs to GitHub Actions and receive completion callbacks. If workflow-dispatch permission is unavailable, it falls back to a repository-backed render queue (Contents: write), which triggers the same renderer without requiring Actions: write. Completed jobs publish a direct MP4 link and a combined ZIP containing the MP4, editorial TXT, cover, and available channel branding assets; a seven-day workflow artifact remains as backup. Configure these secrets before using the render button:

- Cloudflare Worker secrets: existing `APP_PASSWORD`, `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`, plus `GITHUB_TOKEN` (a GitHub token with Actions: write access, or Contents: write for the automatic queue fallback) and `RENDER_WEBHOOK_SECRET` (a long random value).
- GitHub repository Actions secrets: `RENDER_WEBHOOK_SECRET` (same value as Cloudflare) and, if private YouTube upload is wanted, `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN` (OAuth scope `youtube.upload`).

A push to `main` starts the connected Cloudflare Workers Build (`npx wrangler deploy`). Keep the existing D1 binding and all existing records; migrations are additive. Do not paste secrets into chat or commit them to the repository.

See `docs/IMPLEMENTATION.md`.


## 3.7 safeguards and diagnostics

- The dashboard's **Bulut bağlantıları** panel reports whether the required Cloudflare and GitHub secrets are configured. It never displays secret values.
- The Worker does not ask for a per-clip permission URL or written approval. It only sends Twitch clips whose actual Twitch game category is verified as GTA VI to the renderer. Twitch API access is not copyright permission; the channel operator remains responsible for having reuse rights.
- The renderer accepts HTTPS Twitch clip URLs only. Its local-file test mode is enabled only inside the isolated CI test environment.
- Voiceovers longer than 59.9 seconds are rejected rather than silently cut off.
- YouTube API uploads remain private; there is no automatic public scheduling. Review rights, edits and metadata before manually publishing.
- CI includes helper tests and a synthetic end-to-end 1080x1920 MP4 render. This test does not verify a real Twitch clip, Cloudflare deployment, or YouTube OAuth credentials.
