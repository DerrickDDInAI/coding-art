"""Turn a folder of still images into a video file.

How a video file is written with OpenCV
---------------------------------------
A video is just a sequence of images ("frames") plus two pieces of metadata:

* **fps** — how many frames are shown per second. This is what converts a frame
  count into a duration: 250 frames at 25 fps is a 10-second clip.
* **codec** (a "fourcc", four character code) — the algorithm used to compress
  the frames. ``mp4v`` is the safe default here because it ships with almost
  every OpenCV build and plays everywhere. ``avc1`` / ``H264`` compress much
  better but depend on codecs your OpenCV build may not have. Note the fourcc is
  case-sensitive: ``MP4V`` works but makes FFmpeg print a "tag not supported,
  fallback" warning, because the tag registered for MPEG-4 Part 2 is lowercase.

Two rules trip up almost everyone the first time:

1. **Every frame must have exactly the frame size given to ``VideoWriter``.**
   OpenCV does not resize for you and does not raise — it silently discards
   mismatched frames, and you end up with a 0-byte or 1-frame file.
2. **``VideoWriter`` expects BGR**, which is what ``cv2.imread`` gives you, so
   no colour conversion is needed here (unlike GIFs — see ``giffer.py``).
"""

# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence
from uuid import uuid4

# import 3rd-party modules
import cv2

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


def create_video(
    img_dir: Optional[str] = None,
    img_path_list: Optional[List[str]] = None,
    out_path: Optional[str] = None,
    codec: str = "mp4v",
    fps: int = 25,
    img_extensions: Iterable[str] = IMAGE_EXTENSIONS,
    recursive: bool = True,
    sort_img_list: bool = True,
    reverse_img_list: bool = False,
    shuffle_img_list: bool = False,
    duplicate_start_img_amount: int = 0,
    duplicate_end_img_amount: int = 0,
    out_img_shape: Optional[Sequence[int]] = None,
    resize_fct: Optional[Callable] = None,
    rotate_90: Optional[int] = None,
) -> str:
    """Render the images of a folder and/or an explicit list into a video file.

    Arguments:
    * img_dir: folder holding the frames (searched recursively by default).
    * img_path_list: explicit frame paths, appended to whatever ``img_dir`` finds.
    * out_path: where to write. If ``None``, a random unique ``.mp4`` name is used
      so that two runs never overwrite each other.
    * codec: fourcc string, four characters (``MP4V``, ``avc1``, ``XVID``...).
    * fps: frames per second; duration = number of frames / fps.
    * out_img_shape: ``(height, width)`` of the video. Defaults to the shape of
      the first frame.
    * resize_fct: pass ``resize_with_pad`` or ``resize_with_crop`` to keep the
      aspect ratio of frames whose shape differs from the target.
    * rotate_90: counter-clockwise quarter turns applied to every frame.
    * duplicate_start_img_amount / duplicate_end_img_amount: hold the first/last
      frame for this many extra frames.

    Returns: the path the video was written to.
    """
    # a fourcc is literally four characters; anything else silently produces a
    # broken writer, so reject it here where the message is still useful
    if len(codec) != 4:
        raise ValueError(f"codec must be a 4-character fourcc string, got {codec!r}")

    frame_paths = collect_frame_paths(
        img_dir=img_dir,
        img_path_list=img_path_list,
        img_extensions=img_extensions,
        recursive=recursive,
        sort_img_list=sort_img_list,
        reverse_img_list=reverse_img_list,
        shuffle_img_list=shuffle_img_list,
    )

    # the writer needs its frame size up front, before any frame is written
    out_img_height, out_img_width = probe_output_shape(frame_paths, out_img_shape, rotate_90)

    if out_path is None:
        out_path = f"{uuid4()}.mp4"

    # create the destination folder if the caller pointed at one that is missing,
    # otherwise VideoWriter fails silently and leaves you with no file at all
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*codec)

    # frameSize is (width, height) — the cv2 order, not the NumPy one
    out_video = cv2.VideoWriter(
        filename=str(out_path),
        fourcc=fourcc,
        fps=fps,
        frameSize=(out_img_width, out_img_height),
    )

    if not out_video.isOpened():
        raise RuntimeError(
            f"Could not open a video writer for {out_path!r} with codec {codec!r}. "
            "The codec is probably not available in this OpenCV build — try 'MP4V'."
        )

    # try/finally so the file is always finalised, even if a frame fails to read.
    # Without release() the video header is never written and the file is unplayable.
    try:
        for img in iter_frames(
            frame_paths,
            out_img_shape=(out_img_height, out_img_width),
            resize_fct=resize_fct,
            rotate_90=rotate_90,
            duplicate_start_img_amount=duplicate_start_img_amount,
            duplicate_end_img_amount=duplicate_end_img_amount,
        ):
            out_video.write(img)
    finally:
        out_video.release()

    return str(out_path)
