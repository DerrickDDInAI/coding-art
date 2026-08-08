"""Turning images into images, videos and GIFs.

* ``get_resize_interpolation`` - choose INTER_AREA vs INTER_CUBIC.
* ``resizer``                  - change shape without distorting (pad or crop).
* ``frame_sequence``           - collect, order, resize and hold frames.
* ``videographer``             - folder of images -> MP4.
* ``giffer``                   - folder of images -> animated GIF.

``audio.md`` in this folder has the ffmpeg one-liners for muxing a soundtrack
onto a rendered video.
"""
