# Production implementation status

## Active pipeline

- Cloudflare Worker discovers public Twitch clips using Twitch Helix.
- Only clips with Twitch's verified Grand Theft Auto VI game category are eligible.
- The system does not request a permission URL or per-clip written approval. Twitch access/category verification is not a copyright license; the channel operator remains responsible for reuse rights.
- Editorial packages are generated from clip title/metadata. They include a hook, original commentary draft, captions, editing notes, SEO description, tags and hashtags.
- Cloudflare Cron runs every three hours and dispatches one render job per cycle (up to eight per day when eligible clips and compute quota are available).
- GitHub Actions downloads the Twitch clip, analyzes media, trims long silent gaps, renders 1080x1920 H.264/AAC, applies available branding, creates a unique cover from the actual clip frame, and creates MP4/TXT/cover/branding ZIP delivery files.
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

## Branding assets currently in the repository

- `branding/logo.png` is present and used as the persistent logo overlay.
- `banner.png`, `subscribe.png`, `notification.png`, and `outro.png` are optional renderer inputs but are not currently present in the repository.
- Three JPG image assets are present; their intended role must be confirmed before assigning them to overlay slots.
- A unique per-video cover is generated from a frame of that video's own footage.

## Verification limits

CI can verify syntax, unit tests, synthetic rendering, and package construction. It cannot prove that Twitch currently returns downloadable media, that the channel's OAuth credentials are valid, that YouTube accepts scheduled publication, or that every desired branding asset is present. A real end-to-end clip render and YouTube scheduled upload are required before calling the full production workflow verified.

Never reset D1 or delete existing source/draft records.