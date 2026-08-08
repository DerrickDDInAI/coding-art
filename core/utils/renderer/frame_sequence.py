"""Shared plumbing for turning a folder of images into an ordered stream of frames.

Both the video writer (:mod:`core.utils.renderer.videographer`) and the GIF
writer (:mod:`core.utils.renderer.giffer`) need exactly the same four things:

1. collect the image paths,
2. put them in a deliberate order (sorted, reversed or shuffled),
3. force every frame to the same size — a video/GIF container has ONE frame size,
   and a frame of the wrong shape is either rejected or silently dropped,
4. hold the first and last frame for a moment so a looping animation is readable.

Keeping that logic in one place means a fix to the resizing rules benefits both
writers, instead of being fixed in one and forgotten in the other.
"""

# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from pathlib import Path
from random import shuffle as shuffle_in_place
from typing import Callable, Iterable, Iterator, List, Optional, Sequence, Tuple

# import 3rd-party modules
import cv2
import numpy as np

# import local modules
from core.utils.image_pather import IMAGE_EXTENSIONS, get_img_paths
from core.utils.renderer.get_resize_interpolation import get_interpolation

# =====================================================================
# Define functions
# =====================================================================


def collect_frame_paths(
    img_dir: Optional[str] = None,
    img_path_list: Optional[List[str]] = None,
    img_extensions: Iterable[str] = IMAGE_EXTENSIONS,
    recursive: bool = True,
    sort_img_list: bool = True,
    reverse_img_list: bool = False,
    shuffle_img_list: bool = False,
) -> List[str]:
    """Build the ordered list of frame paths that will become the animation.

    ``img_dir`` and ``img_path_list`` can be combined: paths found in the folder
    are appended to the explicit list. This is how you stitch a rendered sequence
    onto a hand-picked intro frame.

    Ordering rules (in priority order):
    * ``shuffle_img_list`` wins — a shuffled sequence has no meaningful sort.
    * otherwise ``sort_img_list`` sorts alphabetically, ``reverse_img_list``
      plays the sequence backwards.
    """
    # never default a mutable list in the signature: Python would create it once
    # and reuse the same list across every call, so frames from one render would
    # leak into the next
    frame_paths = list(img_path_list) if img_path_list else []

    if img_dir is not None:
        frame_paths.extend(
            get_img_paths(
                Path(img_dir),
                extensions=img_extensions,
                recursive=recursive,
                sort=False,  # ordering is decided once, below
            )
        )

    if not frame_paths:
        raise ValueError(
            "No frames to render. Check img_dir / img_path_list and the expected file extensions."
        )

    if shuffle_img_list:
        shuffle_in_place(frame_paths)
    elif sort_img_list:
        frame_paths.sort(reverse=reverse_img_list)

    return frame_paths


def read_frame(img_path: str) -> np.ndarray:
    """Read one frame from disk, failing loudly instead of returning ``None``."""
    img = cv2.imread(img_path)

    # cv2.imread returns None for a missing file, an unsupported format or a
    # truncated download. Without this check the error surfaces much later as a
    # confusing "NoneType has no attribute shape".
    if img is None:
        raise FileNotFoundError(f"OpenCV could not read the frame: {img_path}")

    return img


def fit_frame(
    img: np.ndarray,
    out_img_shape: Sequence[int],
    resize_fct: Optional[Callable] = None,
) -> np.ndarray:
    """Force one frame to ``out_img_shape`` = ``(height, width)``.

    * With ``resize_fct`` (e.g. ``resize_with_pad`` / ``resize_with_crop``) the
      aspect ratio is preserved by padding or cropping.
    * Without it we resize directly, which *will* distort frames whose aspect
      ratio differs from the target. That is fine when every frame already has
      the same shape, which is the common case.
    """
    out_img_height, out_img_width = out_img_shape[:2]

    if resize_fct is not None:
        return resize_fct(img=img, ref_img_shape=(out_img_height, out_img_width))

    # source is the frame we hold, target is the output size — getting these two
    # the right way round is what decides between INTER_AREA and INTER_CUBIC
    interpolation = get_interpolation(
        src_img_shape=img.shape,
        out_img_shape=(out_img_height, out_img_width),
    )

    # None means the frame is already the right size: skip the resize entirely
    if interpolation is None:
        return img

    # cv2.resize takes (width, height) — the opposite of the NumPy order
    return cv2.resize(img, (out_img_width, out_img_height), interpolation=interpolation)


def iter_frames(
    frame_paths: Sequence[str],
    out_img_shape: Optional[Sequence[int]] = None,
    resize_fct: Optional[Callable] = None,
    rotate_90: Optional[int] = None,
    duplicate_start_img_amount: int = 0,
    duplicate_end_img_amount: int = 0,
) -> Iterator[np.ndarray]:
    """Yield every frame of the animation, ready to be written.

    Frames are yielded one at a time (a generator) rather than collected into a
    list: a 1000-frame 4K sequence would be ~25 GB in RAM, but only one frame at
    a time is ever needed by a video or GIF writer.

    Arguments:
    * out_img_shape: ``(height, width)``. If ``None``, the shape of the first
      frame becomes the output shape.
    * rotate_90: number of counter-clockwise quarter turns (``np.rot90``). Use
      ``1`` or ``3`` to turn a landscape sequence into a portrait one.
    * duplicate_start_img_amount / duplicate_end_img_amount: extra copies of the
      first / last frame, so a looping GIF pauses on them instead of flashing by.
    """
    nb_frames = len(frame_paths)

    for frame_nb, img_path in enumerate(frame_paths, start=1):
        img = read_frame(img_path)

        if rotate_90:
            # np.rot90 returns a *view* with a rotated layout; ascontiguousarray
            # copies it back into a normal memory layout, which OpenCV and the
            # video writers require
            img = np.ascontiguousarray(np.rot90(img, rotate_90))

        # the first frame defines the output shape when the caller did not
        if out_img_shape is None:
            out_img_shape = img.shape[:2]

        img = fit_frame(img, out_img_shape, resize_fct=resize_fct)

        # hold on the first frame
        if frame_nb == 1:
            for _ in range(duplicate_start_img_amount):
                yield img

        yield img

        # hold on the last frame
        if frame_nb == nb_frames:
            for _ in range(duplicate_end_img_amount):
                yield img


def probe_output_shape(
    frame_paths: Sequence[str],
    out_img_shape: Optional[Sequence[int]] = None,
    rotate_90: Optional[int] = None,
) -> Tuple[int, int]:
    """Work out the final ``(height, width)`` before writing a single frame.

    A video writer has to be told its frame size up front, so we peek at the
    first frame. ``rotate_90`` with an odd number of turns swaps the two axes,
    which is easy to forget and produces a video where every frame is rejected.
    """
    if out_img_shape is not None:
        return int(out_img_shape[0]), int(out_img_shape[1])

    height, width = read_frame(frame_paths[0]).shape[:2]

    # odd number of quarter turns -> portrait becomes landscape and vice versa
    if rotate_90 and rotate_90 % 2 == 1:
        height, width = width, height

    return height, width
