# GTA6 Shorts Factory — VI RUSH

Automated Twitch GTA VI clip discovery, rights-aware vertical editing, visual duplicate screening and YouTube Shorts publishing for **@VIRUSHGTA6**.

## Current publishing safeguards

1. Discover Twitch clips and verify the GTA VI category.
2. Require a per-broadcaster YouTube reuse permission record, a maximum permitted source-footage duration, a separate audio/music-rights record and a game-footage rights basis.
3. Enforce the permitted source-footage limit when selecting the highlight; only the permitted amount of creator footage can enter the final Short.
4. Render a 1080×1920 H.264/AAC video using a sharp early gameplay frame for a 0.30-second opening card.
5. Reject persistent streamer face-cam overlays, heavily blurred footage and strong visual-content matches to earlier published Shorts.
6. Save visual frame fingerprints with published markers. A serialized render batch prevents a second candidate from racing ahead before the previous upload marker is saved.
7. Generate a clip-specific English title, description, creator credit, relevant tags and 3–5 topic hashtags.
8. Upload publicly to YouTube and report the result to the Worker.

The visual face/blur checks are deterministic OpenCV heuristics, not a perfect AI classifier. The visual duplicate fingerprint compares ordered perceptual hashes of gameplay frames and is designed to catch re-uploads from different Twitch accounts; it is a strong similarity check, not a legal originality determination.

## Rights and copyright — important

A Twitch download URL is not the same as permission to republish the clip on YouTube. A streamer's permission also does not, by itself, grant rights to Rockstar/Take-Two game footage or third-party music/audio inside the recording.

The dashboard has a **Yayıncı ve oyun görüntüsü kullanım izinleri** panel. Record each broadcaster separately, including:
The renderer supports source-footage windows up to 175 seconds. The default new permission value is 120 seconds; every published render is still capped by the specific creator's approved maximum and current authorization evidence.

- the written creator permission evidence;
- the maximum source-footage seconds allowed;
- expiry date, if any;
- separate audio/music rights evidence;
- the basis for using GTA VI game footage.

Rockstar's public fan-use policy is generally limited to non-commercial use. A monetized or promotional channel should not rely on that general fan-use policy as a commercial licence; obtain written publisher permission or another valid rights basis. When rights are unclear, the source must not be published. See the [Rockstar policy](https://support.rockstargames.com/articles/7bNaeoMFTV0iUDGhStTXvz/policy-on-posting-copyrighted-rockstar-games-material).

## Twitch discovery and creator prioritization

The discovery worker paginates the actual GTA VI category clip feed (up to 1,000 clip records per cycle), removes duplicate clip IDs, and checks the corresponding public Twitch channel profiles in batches. Channels are only prioritized as women-led when the channel bio contains an explicit self-description such as "I'm a woman" or "female streamer/creator". The system does not infer gender from usernames, avatars, pronouns, or game category. Other verified GTA VI creators remain eligible in the general pool.

This profile signal affects discovery order only. It is not evidence of permission to reuse a stream, creator voice, music, or game footage; the existing publishing rights checks remain in force.
The deployment workflow checks the live `/api/system/status` version using the existing render webhook secret (the status endpoint is not opened publicly) and verifies that the production discovery response contains pagination/profile-lookup metrics (unless Twitch itself returns a discovery error). This prevents a stale Worker response from being silently reported as a successful deployment.

The women-creator lane checks six source-backed GTA VI Twitch candidates by their actual Twitch login on every cycle. Only accounts returned by Twitch and clips carrying the exact GTA VI game ID are prioritised; deleted, renamed, unavailable, or non-GTA-VI channels/clips are skipped. The general GTA VI category feed remains open to all creators. Source list: Her Campus, “6 Female Twitch Streamers Playing ‘GTA 6’ To Watch” (https://www.hercampus.com/culture/female-twitch-streamers-gta-6/).

## Publishing batch

The Worker runs every three hours (`0 */3 * * *` UTC). Each batch targets **5–10 successful public YouTube uploads**, not merely 5–10 render attempts. It can try up to 50 candidates. Quality, visual-duplicate, permission, source and upload failures are replaced with the next eligible source. If fewer than five properly licensed and technically usable clips exist, the batch is marked underfilled rather than pretending the target was met.

## YouTube metadata and cover

- Titles are generated from each source's clip title/topic and editorial angle; generic repeated title templates are avoided.
- Descriptions open with two lines that describe the actual clip and include source credit, a question and a VI RUSH subscription prompt.
- Tags include GTA VI terms plus relevant topic-specific search phrases. YouTube says title, thumbnail and description are more important for discovery than tags; tags play a minimal role except for common misspellings.
- The cover is selected from a sharp early gameplay frame. YouTube's `thumbnails.set` accepts the existing `youtube.upload` scope; when read scope is unavailable, the uploader keeps the 120-second processing buffer and then calls the thumbnail API instead of skipping the cover.
- Shorts custom thumbnail availability also depends on channel verification/eligibility and YouTube's current account workflow.

## Required configuration

**Cloudflare Worker secrets**
- `APP_PASSWORD`
- `TWITCH_CLIENT_ID`
- `TWITCH_CLIENT_SECRET`
- `GITHUB_TOKEN`
- `RENDER_WEBHOOK_SECRET`

**GitHub Actions secrets**
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`
- `RENDER_WEBHOOK_SECRET`
- `OPENAI_API_KEY` (used only where the configured editorial/visual review actually calls it)

The current YouTube refresh-token test confirmed `youtube.upload`. That scope is sufficient for new video uploads and `thumbnails.set`; a missing `youtube.readonly` scope must not disable the new video's cover. Without read scope, the uploader waits 120 seconds before setting the cover; read scope enables exact processing-status polling. `youtube.force-ssl` and `yt-analytics.readonly` are optional for existing-video metadata edits and Analytics API reports and are not required for the new-video publishing flow.

## Existing channel audit

Do not automatically delete, dispute, unlist or re-upload previously published videos. The new safeguards prevent future risky sources; they do not remove an existing Content ID claim or copyright strike.

Audit existing Shorts in YouTube Studio > Content > Restrictions. Separate Content ID claims from copyright takedowns/strikes, verify each source and audio licence, and compare source duration to the creator's permission. This workflow is audit-only: it does not edit, replace, unlist, dispute or re-upload existing videos.

The detailed 53-video audit sequence, 10-point pre-publish checklist, 20 title examples, description structure and five Shorts analytics metrics are in [VI RUSH Channel Operations](docs/VI-RUSH-CHANNEL-OPERATIONS.md).

## Cloud resources

- Cloudflare Worker: `gta6-shorts-engine`
- D1 database: `gta6-shorts-db`
- Renderer: `.github/workflows/render-short.yml`
- Historical visual fingerprint audit: `.github/workflows/backfill-published-fingerprints.yml`

Preserve all existing D1 records, including imported Twitch sources. Schema changes must be additive. Never commit API keys, tokens, cookies or temporary media URLs.
