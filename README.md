# GTA6 Shorts Factory

Twitch-to-YouTube Shorts production workflow.

## Product direction

Twitch is the **source platform**. The system discovers GTA VI clips on Twitch, resolves clip metadata through the official Twitch API, checks whether the connected Twitch account is authorized to download each clip, and prepares authorized source media for Shorts production. YouTube is only the publishing destination.

The system does not broadcast livestreams, use PostMassive, or scan a YouTube channel for source footage.

## Existing cloud resources

- Cloudflare Worker: `gta6-shorts-engine`
- D1 database: `gta6-shorts-db`
- GitHub Actions renderer: `.github/workflows/render-short.yml`

Preserve all existing D1 source records, including the 127 previously imported Twitch sources. Schema changes must be additive; never reset or delete source records.

## Twitch access

The dashboard connects to Twitch using OAuth at `/auth/twitch/callback`. The Worker uses the configured `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`, and `APP_PASSWORD` secrets. OAuth tokens are encrypted before storage in D1 and refreshed when needed.

Clip slugs are resolved through `GET /helix/clips`. Authorized download links are requested through `GET /helix/clips/downloads` in batches of no more than 10 clip IDs per broadcaster. Temporary Twitch download URLs are used immediately and must not be stored permanently. Clips for broadcasters without editor access are marked unauthorized and skipped on future checks.

Technical Twitch download access is **not** commercial reuse permission. Rights review remains a separate decision and must not be inferred from OAuth access.

## Renderer

The renderer downloads authorized Twitch clips, checks media streams, selects a 55-second high-activity window from longer videos using audio activity and scene changes, trims long silent gaps, preserves original source audio without AI voice or added music, creates a 1080x1920 H.264/AAC MP4, generates a separate cover, and packages the MP4, editorial TXT, cover, and branding assets into a ZIP.

The renderer rejects localhost/private-network URLs and non-HTTPS sources. A public clip or a technically downloadable clip is not automatically cleared for reuse. Human rights review remains required.

## Branding assets

The supplied logo and three JPG channel graphics are stored in `branding/`. The logo is applied persistently. Subscribe and notification artwork is converted to transparent PNG overlays and displayed during the final seconds. The wide VI RUSH artwork remains included in the ZIP.

## YouTube

YouTube is the publishing destination only. Optional OAuth uploads are private by default. No automatic public publishing is performed; review the clip rights, edit, title, description, and thumbnail before changing visibility.

Never commit credentials, OAuth tokens, cookies, temporary Twitch download URLs, or private source URLs.
