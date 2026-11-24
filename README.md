# GTA6 Shorts Factory

Automated Twitch-to-YouTube Shorts factory for the **@VIRUSHGTA6** channel.

## Automatic pipeline

1. Discover GTA VI clips on Twitch through the Twitch Helix API.
2. Resolve clip metadata and verify the GTA VI game category.
3. Download public Twitch clip media in the GitHub Actions renderer with yt-dlp. **No personal Twitch account OAuth or editor permission is required for public clips.**
4. Render a vertical 1080x1920 H.264/AAC Short, select an active highlight, trim dead air, preserve source audio, add English AI narration when an editorial script is available, and apply the supplied branding assets.
5. Run a vision review of sampled clip frames, reject explicit sexual content and low-interest footage, and classify non-explicit mature scenes for a tailored edit and age-review handling. Generate an English title, description, tags, hashtags, cover, editorial TXT and ZIP package.
6. Upload standard clips publicly to YouTube and report the video URL to the dashboard. Clips flagged for an age gate are uploaded privately because the YouTube Data API does not expose a creator-set age-restriction control; they must not be made public without the appropriate platform age gate.

The system does not broadcast livestreams, use PostMassive, or use YouTube as a source platform.

## Cloud resources

- Cloudflare Worker: `gta6-shorts-engine`
- D1 database: `gta6-shorts-db`
- GitHub Actions renderer: `.github/workflows/render-short.yml`

Preserve all existing D1 records, including the 127 imported Twitch sources. Schema changes must be additive; never reset or delete source records.

## Required configuration

Worker secrets:
- `APP_PASSWORD`
- `TWITCH_CLIENT_ID` and `TWITCH_CLIENT_SECRET` (Twitch app credentials for public clip discovery, not personal account OAuth)
- `GITHUB_TOKEN`
- `RENDER_WEBHOOK_SECRET`

GitHub Actions secrets:
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`
- `RENDER_WEBHOOK_SECRET`

The YouTube OAuth refresh token must belong to the **@VIRUSHGTA6** channel and include the YouTube upload scope. The uploader fails visibly if credentials are missing; it never silently skips publishing.

## Rendering and delivery

The renderer selects a high-activity window from longer source media, trims long silent gaps, preserves original audio, adds an English AI voiceover when a suitable editorial script is available, creates a 1080x1920 MP4, generates a cover and packages the MP4, TXT, cover, analysis and branding into a ZIP. Releases and GitHub Actions artifacts provide download links.

The scheduled Worker runs every three hours, discovers clips, prepares packages and dispatches the next queued render. Completed jobs update the dashboard with render status, YouTube status and public video URL.

## Branding

The supplied logo and channel artwork are stored in `branding/`. The logo is applied as a watermark during gameplay; the supplied VI RUSH artwork is used for opening and closing cards; subscribe and notification overlays appear near the end of the Short. Non-explicit mature scenes receive a `MATURE THEMES` notice when the visual review classifies them for mature treatment. The generated cover is included in the package; YouTube custom-thumbnail upload requires channel eligibility/verification and may fail until enabled.

Never commit credentials, OAuth tokens, cookies or temporary media URLs.
