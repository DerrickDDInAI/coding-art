"""Resize an image to a target shape *without distorting it*.

The problem
-----------
``cv2.resize(img, (width, height))`` happily stretches a portrait photo into a
landscape frame, which makes faces look squashed. When you assemble frames of
different shapes into one video or GIF, every frame must end up the exact same
size, so you need a way to change the shape while keeping the **aspect ratio**
(width / height) intact. There are only two honest ways to do that:

1. **Pad** ("letterbox") — keep the whole image, add black bars on the two sides
   that are too short. Nothing is lost, but the subject gets smaller.
   ``resize_with_pad``

2. **Crop** — fill the whole frame, throw away the parts that stick out.
   Nothing is distorted and nothing is shrunk, but the edges are lost.
   ``resize_with_crop``

Both functions do the shape correction *first* (on the original pixels) and only
then hand the result to ``cv2.resize``. Doing it the other way round would resize
twice and lose detail for nothing.

Remember the axis convention: NumPy shapes are ``(height, width, channels)``
while ``cv2.resize`` wants ``(width, height)``. Every flip in this file is
deliberate.
"""

# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from typing import Optional, Sequence, Tuple

# import 3rd-party modules
import cv2
import numpy as np

# import local modules
from core.utils.renderer.get_resize_interpolation import get_interpolation

# =====================================================================
# Define helper functions
# =====================================================================


def _load_image(img: Optional[np.ndarray], img_path: Optional[str]) -> np.ndarray:
    """Return an image array, reading it from disk if only a path was given."""
    if img is None and img_path is None:
        raise ValueError("Provide either an image array (img) or an image path (img_path).")

    if img_path is not None:
        img = cv2.imread(img_path)
        # cv2.imread does NOT raise on a missing/corrupt file: it quietly returns
        # None, and the crash then happens far away in the pipeline. Check here.
        if img is None:
            raise FileNotFoundError(f"OpenCV could not read the image: {img_path}")

    return img


def _resolve_ref_shape(
    ref_img: Optional[np.ndarray],
    ref_img_path: Optional[str],
    ref_img_shape: Optional[Sequence[int]],
) -> Tuple[int, int]:
    """Return the reference ``(height, width)`` from whichever form the caller gave."""
    # an explicit shape wins: it saves us from decoding a whole reference image
    # just to read two numbers off it
    if ref_img_shape is not None:
        return int(ref_img_shape[0]), int(ref_img_shape[1])

    if ref_img is None and ref_img_path is not None:
        ref_img = cv2.imread(ref_img_path)
        if ref_img is None:
            raise FileNotFoundError(f"OpenCV could not read the reference image: {ref_img_path}")

    if ref_img is None:
        raise ValueError("Provide one of: ref_img, ref_img_path or ref_img_shape.")

    return int(ref_img.shape[0]), int(ref_img.shape[1])


def _to_cv2_size(height: int, width: int) -> Tuple[int, int]:
    """Flip a NumPy ``(height, width)`` pair into the ``(width, height)`` cv2 wants."""
    return (width, height)


# =====================================================================
# Define functions
# =====================================================================


def resize_with_pad(
    img: Optional[np.ndarray] = None,
    ref_img: Optional[np.ndarray] = None,
    img_path: Optional[str] = None,
    ref_img_path: Optional[str] = None,
    ref_img_shape: Optional[Sequence[int]] = None,
    cvt_color: Optional[int] = None,
    pad_color: int = 0,
) -> np.ndarray:
    """Resize ``img`` to the reference shape, adding bars to preserve the aspect ratio.

    Arguments:
    * img / img_path: the image to resize, as an array or a path on disk.
    * ref_img / ref_img_path / ref_img_shape: the target, in any of three forms.
    * cvt_color: an optional ``cv2.COLOR_*`` flag applied to the image before
      resizing (e.g. ``cv2.COLOR_BGR2LAB``). Leave as ``None`` to keep BGR.
    * pad_color: value used for the bars; ``0`` is black, ``255`` white.

    Returns: an image of exactly the reference height and width.
    """
    img = _load_image(img, img_path)

    # optional colour-space conversion. OpenCV loads images as BGR, but some
    # algorithms (colour matching in particular) work far better in LAB, where
    # distance between colours roughly matches how different they look to a human.
    if cvt_color is not None:
        img = cv2.cvtColor(img, cvt_color)

    ref_img_height, ref_img_width = _resolve_ref_shape(ref_img, ref_img_path, ref_img_shape)

    img_height, img_width = img.shape[:2]

    # aspect ratio = width / height. Bigger number means "wider".
    img_ratio = img_width / img_height
    ref_img_ratio = ref_img_width / ref_img_height

    if img_ratio == ref_img_ratio:
        # already the right proportions: a plain resize will not distort anything
        padded_img = img

    elif img_ratio < ref_img_ratio:
        # the image is narrower than the target -> pad left and right
        new_width = round(img_height * ref_img_ratio)
        padded_img = np.full((img_height, new_width, *img.shape[2:]), pad_color, dtype=img.dtype)

        # integer division centres the image; a 1-pixel remainder ends up on the
        # right, which is invisible and keeps the arithmetic simple
        y, x = 0, (new_width - img_width) // 2
        padded_img[y : y + img_height, x : x + img_width] = img

    else:
        # the image is wider than the target -> pad top and bottom
        new_height = round(img_width / ref_img_ratio)
        padded_img = np.full((new_height, img_width, *img.shape[2:]), pad_color, dtype=img.dtype)

        y, x = (new_height - img_height) // 2, 0
        padded_img[y : y + img_height, x : x + img_width] = img

    # Pick the interpolation from the *padded* image, not the original one: the
    # padding already changed the pixel count, and that is the resize that is
    # actually about to happen.
    interpolation = get_interpolation(
        src_img_shape=padded_img.shape,
        out_img_shape=(ref_img_height, ref_img_width),
    )

    # interpolation is None when the padded image already has the target shape
    if interpolation is None:
        return padded_img

    return cv2.resize(padded_img, _to_cv2_size(ref_img_height, ref_img_width), interpolation=interpolation)


def resize_with_crop(
    img: Optional[np.ndarray] = None,
    ref_img: Optional[np.ndarray] = None,
    img_path: Optional[str] = None,
    ref_img_path: Optional[str] = None,
    ref_img_shape: Optional[Sequence[int]] = None,
    cvt_color: Optional[int] = None,
) -> np.ndarray:
    """Resize ``img`` to the reference shape, cropping from the centre to preserve the aspect ratio.

    Same arguments as :func:`resize_with_pad`, minus ``pad_color`` (nothing is
    added here — the excess is cut away instead).

    Returns: an image of exactly the reference height and width, with no bars and
    no distortion, at the cost of losing the edges of the longer axis.
    """
    img = _load_image(img, img_path)

    if cvt_color is not None:
        img = cv2.cvtColor(img, cvt_color)

    ref_img_height, ref_img_width = _resolve_ref_shape(ref_img, ref_img_path, ref_img_shape)

    img_height, img_width = img.shape[:2]

    img_ratio = img_width / img_height
    ref_img_ratio = ref_img_width / ref_img_height

    if img_ratio == ref_img_ratio:
        # `.copy()` so that callers never mutate the array we were handed
        cropped_img = img.copy()

    elif img_ratio > ref_img_ratio:
        # the image is wider than the target -> cut the left and right edges off
        new_width = round(img_height * ref_img_ratio)
        x = (img_width - new_width) // 2
        cropped_img = img[:, x : x + new_width]

    else:
        # the image is narrower than the target -> cut the top and bottom off
        new_height = round(img_width / ref_img_ratio)
        y = (img_height - new_height) // 2
        cropped_img = img[y : y + new_height, :]

    # again: measure the resize from the cropped image, which is what we resize
    interpolation = get_interpolation(
        src_img_shape=cropped_img.shape,
        out_img_shape=(ref_img_height, ref_img_width),
    )

    if interpolation is None:
        return cropped_img

    return cv2.resize(cropped_img, _to_cv2_size(ref_img_height, ref_img_width), interpolation=interpolation)
