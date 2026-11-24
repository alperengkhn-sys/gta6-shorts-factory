# Channel branding assets

The following supplied assets are already committed in this folder:

- `logo.png` — persistent channel logo; applied to the upper-left corner of every rendered Short.
- `image_50843161.jpg` — wide VI RUSH / Leonida Loop channel artwork with subscribe call-to-action.
- `image_2d2a6dba.jpg` — crocodile subscribe call-to-action graphic.
- `image_c69a04ba.jpg` — notification/bell call-to-action graphic.

The three JPG images have a checkerboard pattern baked into their pixels rather than transparency. They are included in every delivery ZIP, but must be converted to transparent PNG overlays before being placed on top of footage; otherwise the checkerboard would be visible in the video.

The renderer also generates a unique `short-cover.jpg` from a frame of each video's actual footage and includes it in the delivery package. When YouTube upload is configured, this cover is submitted as the thumbnail.
