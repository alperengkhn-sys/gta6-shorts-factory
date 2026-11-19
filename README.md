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
5. Require recorded rights approval before rendering or upload.
6. Default YouTube uploads to private until explicitly reviewed.
7. Treat free compute quotas as hard limits; never claim unlimited free rendering.

## Deployment

The repository contains the 3.5 Worker, Wrangler configuration, and a GitHub Actions cloud renderer. The Worker can dispatch approved draft jobs to GitHub Actions and receive completion callbacks. Configure these secrets before using the render button:

- Cloudflare Worker secrets: existing `APP_PASSWORD`, `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`, plus `GITHUB_TOKEN` (a GitHub token with Actions: write access to this repository) and `RENDER_WEBHOOK_SECRET` (a long random value).
- GitHub repository Actions secrets: `RENDER_WEBHOOK_SECRET` (same value as Cloudflare) and, if private YouTube upload is wanted, `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN` (OAuth scope `youtube.upload`).

A push to `main` starts the connected Cloudflare Workers Build (`npx wrangler deploy`). Keep the existing D1 binding and all existing records; migrations are additive. Do not paste secrets into chat or commit them to the repository.

See `docs/IMPLEMENTATION.md`.
