# Implementation notes

## Platform responsibilities

- Twitch is the sole source platform for automatic clip discovery and source download.
- YouTube is the destination for finished Shorts; it is not a source-discovery target.
- No PostMassive, live broadcast, or stream publishing integration is used.

## Twitch integration

- OAuth callback: `/auth/twitch/callback`.
- Secrets: `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`, and `APP_PASSWORD`.
- Access and refresh tokens are encrypted in D1; refresh is attempted when validation fails.
- Clip slugs resolve through Twitch Helix `/clips`; category metadata is checked against Grand Theft Auto VI.
- Authorized download requests use `/clips/downloads`, grouped by broadcaster and sent in batches of at most 10 clip IDs.
- Temporary download URLs are not persisted. Broadcasters without editor permission are marked unauthorized and skipped.
- The 127 existing source records must be preserved. Twitch download authorization and commercial reuse rights are separate states.

## Rendering

The renderer produces vertical 1080x1920 H.264/AAC Shorts, preserves original source audio, removes long silent gaps, selects a high-activity section from longer videos, applies the supplied branding, generates a cover, and packages the MP4 plus editorial metadata and assets into a ZIP. It does not add AI narration or music.

## Validation still required

- Verify the existing Twitch OAuth connection and token refresh against the deployed Worker.
- Process the existing Twitch sources in small batches; report resolved, downloadable, unauthorized, unavailable, and error counts.
- Test a real authorized Twitch clip through MP4 render and ZIP download.
- Verify the optional private YouTube upload only after a successful real render.

Do not reset D1. Do not store temporary Twitch download URLs. Do not treat technical download permission as copyright or commercial-use permission.
