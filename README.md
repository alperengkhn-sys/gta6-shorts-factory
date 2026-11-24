# GTA6 Shorts Factory

Cloud-first video-to-YouTube-Shorts production workflow.

## Product direction

This system prepares edited vertical Shorts from **video/clip sources that the operator is authorized to reuse**. It can scan recent public channel/video-tab/playlist entries for GTA VI titles and can also accept a direct video URL. It does not broadcast livestreams or require a streaming-platform account connection.

## Existing cloud resources

- Cloudflare Worker: `gta6-shorts-engine`
- D1 database: `gta6-shorts-db`
- GitHub Actions renderer: `.github/workflows/render-short.yml`

Preserve existing D1 tables and records. Use additive migrations only. Never commit credentials, OAuth tokens, cookies, or private source URLs.

## Renderer

The GitHub Actions renderer accepts public HTTPS video/clip URLs supported by yt-dlp, downloads the source, checks media streams, selects a 55-second high-activity window from longer videos using audio activity and scene changes, trims long silent gaps, creates a 1080x1920 H.264/AAC MP4, generates a frame-based cover, and packages the MP4, editorial TXT, cover, and branding assets into a ZIP. It also publishes a direct MP4/package release link when GitHub Releases permissions allow it.

The renderer rejects localhost/private-network URLs and non-HTTPS sources. Only submit material for which you have the necessary copyright, license, and platform permissions. A URL being publicly accessible is not permission to reuse it. Automated checks cannot guarantee that a clip is copyright-safe; human rights review remains required.

## Branding assets

The supplied logo and three JPG channel graphics are stored in `branding/`. The logo is applied persistently. The workflow removes the checkerboard backgrounds from the subscribe and notification artwork, converts them to transparent PNG overlays, and displays them during the final five seconds. The wide VI RUSH artwork remains included in the ZIP.

## YouTube

Optional YouTube OAuth uploads are private by default. No automatic public publishing is performed. Review rights, edits, title, description, and thumbnail before changing visibility.

Configure secrets only in the relevant Cloudflare/GitHub settings. Never paste secrets into chat or commit them to this repository.

## Validation limits

CI synthetic renders validate the renderer pipeline only. They do not prove that a real third-party source is downloadable, that reuse rights exist, that Cloudflare is deployed, or that YouTube credentials work. See `docs/IMPLEMENTATION.md` for implementation notes.
