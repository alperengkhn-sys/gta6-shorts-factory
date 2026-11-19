# Cloud rendering

## Automatic dashboard flow

1. In Cloudflare Worker settings, configure `GITHUB_TOKEN` (a GitHub token with Actions: write access to this repository) and `RENDER_WEBHOOK_SECRET` (a long random secret). Keep all existing Worker secrets.
2. In GitHub → repository Settings → Secrets and variables → Actions, create `RENDER_WEBHOOK_SECRET` with the exact same value.
3. Open the GTA6 Shorts Factory dashboard and select a draft.
4. Choose **İzin kanıtıyla MP4 üret**. For a source not already marked approved, enter the permission evidence URL or a clear evidence reference. This records the source as approved; do not do it without actual permission.
5. The Worker dispatches the job to GitHub Actions. The workflow renders 1080×1920 H.264/AAC, stores the MP4 as a seven-day artifact, optionally uploads it to YouTube as **private**, and posts status back to the Worker. The dashboard shows the render state, artifact link, and YouTube URL/status.

## Optional private YouTube upload

Create a Google Cloud project, enable **YouTube Data API v3**, and create OAuth credentials that can grant the scope `https://www.googleapis.com/auth/youtube.upload`. Obtain an offline refresh token for the channel and add these GitHub Actions repository secrets: `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, and `YOUTUBE_REFRESH_TOKEN`. When all three are present, every successful render uploads as **private**; public publishing is not enabled. YouTube Data API quota is finite and controls daily upload volume. If the secrets are absent, rendering still completes and the upload step is marked `not_configured`.

## Manual fallback

1. Open the repository's **Actions** tab.
2. Select **Render GTA6 Short** → **Run workflow**.
3. Enter an authorized clip URL, title, original narration, and set rights approval to true only when documented permission exists.
4. Start the workflow and download the artifact after it completes.

## Limits and safeguards

- Cloud rendering only; no local PC processing is required.
- GitHub Actions free usage is quota-limited. This does not guarantee 5–10 renders daily.
- The built-in English voice is synthetic/basic. Captions are timed across narration, not word-level ASR.
- This does not analyze the footage visually or verify ownership. Metadata/title-derived editorial text must be checked against the clip.
- Twitch clip access is not permission to reuse it. Rights-pending sources cannot be rendered through the dashboard flow.
- Artifact retention is seven days. The artifact link requires access to the GitHub repository.
