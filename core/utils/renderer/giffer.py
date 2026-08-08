"""Turn a folder of still images into an animated GIF.

GIF vs video — what is different
--------------------------------
* **Colour order.** OpenCV loads images as **BGR** (blue, green, red) for
  historical reasons, while every other library — imageio included — assumes
  **RGB**. Forgetting the ``cv2.cvtColor(img, cv2.COLOR_BGR2RGB)`` below is the
  single most common bug in this repo's history: the GIF renders fine, but every
  blue sky comes out orange.
* **Colour depth.** A GIF frame can only hold 256 distinct colours. Photographic
  gradients therefore get quantised and can show visible banding. This is a
  limitation of the format, not of the code.
* **Timing.** GIFs store a delay *per frame* rather than a global fps. imageio
  takes that as ``duration`` in **milliseconds**; we accept ``fps`` here and
  convert, so the API matches ``create_video``.
* **Size.** GIFs get large fast. ``pygifsicle.optimize`` rewrites the file
  in place, dropping pixels that do not change between frames. It needs the
  external ``gifsicle`` binary (``brew install gifsicle``), so we degrade
  gracefully to an unoptimised GIF if it is missing.
"""

# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence
from uuid import uuid4
from warnings import warn

# import 3rd-party modules
import cv2
from imageio import get_writer

# import local modules
from core.utils.image_pather import IMAGE_EXTENSIONS
from core.utils.renderer.frame_sequence import (
    collect_frame_paths,
    iter_frames,
    probe_output_shape,
)

# =====================================================================
# Define functions
# =====================================================================


def create_gif(
    img_dir: Optional[str] = None,
    img_path_list: Optional[List[str]] = None,
    out_path: Optional[str] = None,
    fps: int = 25,
    loop: int = 0,
    img_extensions: Iterable[str] = IMAGE_EXTENSIONS,
    recursive: bool = True,
    sort_img_list: bool = True,
    reverse_img_list: bool = False,
    shuffle_img_list: bool = False,
    writer_mode: str = "I",
    duplicate_start_img_amount: int = 0,
    duplicate_end_img_amount: int = 0,
    out_img_shape: Optional[Sequence[int]] = None,
    resize_fct: Optional[Callable] = None,
    rotate_90: Optional[int] = None,
    optimize_gif: bool = True,
) -> str:
    """Render the images of a folder and/or an explicit list into an animated GIF.

    Arguments mirror :func:`core.utils.renderer.videographer.create_video`, plus:
    * fps: frames per second, converted to a per-frame delay for imageio.
    * loop: ``0`` loops forever, ``1`` plays once, ``n`` plays n times.
    * writer_mode: imageio mode; ``"I"`` means "a sequence of images".
    * optimize_gif: shrink the file with ``gifsicle`` afterwards. It can cost a
      little quality, but usually cuts the size by half or more.

    Returns: the path the GIF was written to.
    """
    frame_paths = collect_frame_paths(
        img_dir=img_dir,
        img_path_list=img_path_list,
        img_extensions=img_extensions,
        recursive=recursive,
        sort_img_list=sort_img_list,
        reverse_img_list=reverse_img_list,
        shuffle_img_list=shuffle_img_list,
    )

    # every GIF frame must have the same shape, exactly as for a video
    out_img_height, out_img_width = probe_output_shape(frame_paths, out_img_shape, rotate_90)

    if out_path is None:
        out_path = f"{uuid4()}.gif"

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    # imageio wants the on-screen time of one frame, in milliseconds
    frame_duration_ms = 1000 / fps

    # the context manager guarantees the GIF trailer is written even on error
    with get_writer(out_path, mode=writer_mode, duration=frame_duration_ms, loop=loop) as writer:
        for img in iter_frames(
            frame_paths,
            out_img_shape=(out_img_height, out_img_width),
            resize_fct=resize_fct,
            rotate_90=rotate_90,
            duplicate_start_img_amount=duplicate_start_img_amount,
            duplicate_end_img_amount=duplicate_end_img_amount,
        ):
            # OpenCV hands us BGR, imageio expects RGB — convert or your colours
            # come out swapped (red and blue channels traded)
            writer.append_data(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    if optimize_gif:
        try:
            from pygifsicle import optimize

            # rewrites the file in place
            optimize(out_path)
        except Exception as error:  # noqa: BLE001 - optimisation is a bonus, never fatal
            # A missing `gifsicle` binary is by far the most likely cause. The GIF
            # itself is already written and perfectly valid, so warn and move on.
            warn(f"Could not optimize the GIF ({error}). Install gifsicle to enable it.", stacklevel=2)

    return str(out_path)
