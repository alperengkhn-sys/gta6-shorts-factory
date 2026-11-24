# Channel branding assets

The supplied assets are committed in this folder:

- `logo.png` — persistent channel logo, applied to the upper-left corner of every rendered Short.
- `image_50843161.jpg` — wide VI RUSH / Leonida Loop artwork with a subscribe call-to-action; included in delivery ZIPs.
- `image_2d2a6dba.jpg` — crocodile subscribe call-to-action. The render workflow converts this to `subscribe.png` with the checkerboard background removed and displays it in the final five seconds.
- `image_c69a04ba.jpg` — notification/bell call-to-action. The render workflow converts this to `notification.png` with the checkerboard background removed and displays it in the final five seconds.

The conversion uses a color-based checkerboard-removal heuristic. Review the generated overlays in a real MP4 for edge artifacts before publishing.

The renderer also generates a unique `short-cover.jpg` from a frame of each video's actual footage and includes it in the delivery package. When YouTube upload is configured, this cover is submitted as the thumbnail.
