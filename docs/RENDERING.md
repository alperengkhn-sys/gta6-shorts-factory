# Cloud rendering

The repository now includes a GitHub Actions cloud render job.

## Run

1. Open the repository's **Actions** tab.
2. Select **Render GTA6 Short** → **Run workflow**.
3. Enter an authorized clip URL, title, and original narration.
4. Set rights approval to **true only when you have permission to use the footage**.
5. Start the workflow. When it finishes, open the run and download the `gta6-short-*` artifact.

The runner downloads the source with yt-dlp, creates English narration with espeak-ng, burns captions, renders 1080x1920 H.264/AAC, validates the result, and stores the MP4 as a seven-day workflow artifact.

## Limits

- This is cloud rendering; no local PC processing is required.
- GitHub Actions free usage is quota-limited. This does not guarantee 5–10 renders daily.
- The built-in voice is synthetic and basic. No paid TTS service is used.
- Captions are timed across the narration, not word-level speech recognition.
- It does not claim to analyze the visual content or verify ownership.
- Only use footage you own or are authorized to use. Twitch clip availability is not permission.
- This workflow renders on manual dispatch. Automatic Twitch discovery, editorial review, and YouTube upload still require integration with the existing Cloudflare Worker and YouTube OAuth credentials.
