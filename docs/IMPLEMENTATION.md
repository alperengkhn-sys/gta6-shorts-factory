# Production implementation plan

## Phase 1 — Preserve and harden 3.5

- Keep Twitch OAuth, encrypted token storage, and existing data.
- Add request validation, bounded batches, audit events, and consistent errors.
- Fix GTA VI discovery relevance checks so unrelated clips are not accepted.
- Distinguish clip metadata resolution from actual downloadable media access.

## Phase 2 — Rights workflow

A source is not renderable unless rights status is explicitly approved and evidence is recorded. Technical access, creator permission, and platform policy are separate states. Public availability is not consent.

## Phase 3 — Cloud media runner

Cloudflare Workers are not an FFmpeg runtime. Actual 1080x1920 H.264/AAC rendering needs a separate compute runner. A no-paid-service option is GitHub Actions with open-source FFmpeg, subject to finite free Actions quotas and runtime limits. 5–10 finished videos every day cannot be guaranteed for free.

The runner must accept only approved jobs, use authorized source media, create vertical MP4 with captions and original narration, validate output, store the result, and report job status to the Worker.

## Phase 4 — YouTube

Add YouTube OAuth with least-privilege scopes. Encrypt refresh tokens. Upload privately by default; public publishing requires explicit approval. Never put credentials in source code or logs.

## Phase 5 — Real media analysis

Title heuristics are not visual/audio analysis. Genuine analysis requires a model runtime. No paid inference API is assumed. Until a free runtime is configured and tested, label results metadata-only and do not fabricate observations about footage.

## Acceptance checks

- Existing D1 records survive deployment.
- Twitch OAuth connects and refreshes.
- Discovery excludes unrelated games.
- Duplicate source URLs are rejected.
- Rights-pending items cannot be rendered or uploaded.
- Retries do not create duplicate uploads.
- YouTube uploads remain private by default.
- Rendered files pass codec, dimensions, duration, and size validation.
