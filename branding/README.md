# Channel branding assets

Drop the supplied channel assets here when they are provided. The cloud renderer reads these optional filenames automatically:

- `banner.png` — persistent top banner across the Short.
- `logo.png` — persistent channel logo in the upper-left corner.
- `subscribe.png` — subscribe call-to-action shown during the final five seconds.
- `notification.png` — notification/bell call-to-action shown during the final five seconds.
- `outro.png` — full-frame closing screen shown during the final three seconds.

Use transparent PNGs for overlays where possible. Missing assets are skipped; they do not block rendering. Each render also creates `short-cover.jpg` from a frame of that video's actual footage with its title, and includes it in the downloadable artifact. The cover is also submitted as the YouTube thumbnail when YouTube upload is configured and the channel has thumbnail-upload access.
