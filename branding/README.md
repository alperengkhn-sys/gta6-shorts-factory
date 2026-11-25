# Channel branding assets

The supplied assets are committed in this folder:

- `logo.png` — persistent channel logo, applied to the upper-left corner of every rendered Short.
- `image_50843161.jpg` — VI RUSH / Leonida Loop branded artwork used as the opening bumper and closing end card.
- `image_2d2a6dba.jpg` — crocodile subscribe call-to-action. The render workflow converts this to `subscribe.png` with the checkerboard background removed and displays it during the final five seconds, above the end card.
- `image_c69a04ba.jpg` — notification/bell call-to-action. The render workflow converts this to `notification.png` with the checkerboard background removed and displays it during the final five seconds, above the end card.
- A readable `LIKE • SUBSCRIBE • TURN ON NOTIFICATIONS` text reminder is also rendered during the final five seconds. There is no separate like-image file in this folder.

The conversion uses a color-based checkerboard-removal heuristic. Review the generated overlays in a real MP4 for edge artifacts before publishing. The full-frame intro/outro artwork is composited before the logo and closing CTA overlays so it does not cover the supplied subscribe and bell graphics.

The renderer also generates a unique `short-cover.jpg` from a frame of each video's actual footage and includes it in the delivery package. When YouTube upload is configured, this cover is submitted as the thumbnail.
