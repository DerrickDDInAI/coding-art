"""Pick the right OpenCV interpolation flag for a resize operation.

Computer-vision background: why interpolation matters
-----------------------------------------------------
An image is a grid of pixels. When you resize it, the output grid does not line
up with the input grid, so OpenCV has to *invent* the value of every output
pixel from its neighbours. The rule it uses is the "interpolation" method, and
picking the wrong one is one of the most common sources of ugly results:

* ``cv2.INTER_AREA`` — averages all the input pixels that fall inside an output
  pixel. This is the correct choice when **shrinking**. Because it looks at
  every source pixel, nothing is skipped, so fine detail turns into a clean
  average instead of aliasing (the shimmering / jagged "staircase" artefacts you
  get when a downscaler samples only a few pixels and misses the rest).

* ``cv2.INTER_CUBIC`` — fits a smooth curve through a 4x4 neighbourhood. This is
  the good default when **enlarging**: it produces smoother edges than
  ``INTER_LINEAR`` (2x2 neighbourhood) at a moderate extra cost.

* ``cv2.INTER_NEAREST`` — just copies the closest pixel. Blocky, but it is the
  only correct choice for images whose values are *labels* rather than colours
  (segmentation masks), because averaging label 3 and label 5 into 4 invents a
  class that was never there.

* ``None`` (our own convention, not an OpenCV value) — means "no resize needed".
  Callers use it as a signal to skip ``cv2.resize`` entirely, which is both
  faster and lossless.

Rule of thumb: **shrink with INTER_AREA, grow with INTER_CUBIC.**
"""

# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from typing import Optional, Sequence

# import 3rd-party modules
import cv2

# =====================================================================
# Define functions
# =====================================================================


def get_interpolation(
    src_img_shape: Sequence[int],
    out_img_shape: Optional[Sequence[int]] = None,
    out_img_scale: Optional[Sequence[float]] = None,
) -> Optional[int]:
    """Return the best ``cv2`` interpolation flag, or ``None`` if no resize is needed.

    Arguments:
    * src_img_shape: shape of the source image, in NumPy order ``(height, width)``.
      You can pass ``img.shape`` directly; a third channel entry is ignored.
    * out_img_shape: target shape, also ``(height, width)``.
    * out_img_scale: target scale factors as ``(fy, fx)`` — vertical first, to stay
      consistent with the ``(height, width)`` convention used everywhere else.

    Exactly one of ``out_img_shape`` / ``out_img_scale`` should be given. If both
    are given we raise, because silently letting one win has hidden bugs before.

    Beware of the two conventions:
    NumPy indexes images as ``[row, column]`` = ``(height, width)``, but
    ``cv2.resize`` takes its target size as ``(width, height)``. This function
    speaks NumPy order; remember to flip when you call ``cv2.resize``.
    """
    if out_img_shape is not None and out_img_scale is not None:
        raise ValueError("Pass either out_img_shape or out_img_scale, not both.")

    # source area in pixels — comparing areas (rather than only width or only
    # height) is what tells us whether the image overall grows or shrinks
    src_img_height, src_img_width = src_img_shape[:2]
    src_img_size = src_img_height * src_img_width

    # ------------------------------------------------------------------
    # Case 1: caller gave an explicit target shape
    # ------------------------------------------------------------------
    if out_img_shape is not None:
        out_img_height, out_img_width = out_img_shape[:2]

        # identical shape: nothing to do, tell the caller to skip the resize
        if (out_img_height, out_img_width) == (src_img_height, src_img_width):
            return None

        out_img_size = out_img_height * out_img_width

        # growing (or same pixel count but a different aspect ratio, e.g. a
        # 4:3 image squeezed into 3:4 — some axis is being stretched, so we
        # still want the smoother method)
        if out_img_size >= src_img_size:
            return cv2.INTER_CUBIC

        # shrinking
        return cv2.INTER_AREA

    # ------------------------------------------------------------------
    # Case 2: caller gave scale factors
    # ------------------------------------------------------------------
    if out_img_scale is not None:
        out_img_fy, out_img_fx = out_img_scale

        # scaling by exactly 1.0 on both axes is a no-op
        if (out_img_fy, out_img_fx) == (1.0, 1.0):
            return None

        # the area changes by the product of the two factors
        total_scale_f = out_img_fy * out_img_fx

        if total_scale_f > 1.0:
            return cv2.INTER_CUBIC

        # this covers both shrinking (< 1.0) and the area-preserving-but-
        # distorting case (e.g. fy=2.0, fx=0.5), where one axis is squeezed and
        # INTER_AREA protects that axis from aliasing
        return cv2.INTER_AREA

    # neither target given: there is nothing to resize to
    return None
