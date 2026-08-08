"""Detect faces in a folder of photos and save each face as its own small image.

Computer-vision background: Haar cascades
-----------------------------------------
This uses the Viola-Jones detector (2001), the classic "first face detector".
It is worth understanding because the ideas show up everywhere:

* A **Haar feature** is a crude template: two adjacent rectangles, where the
  detector sums the pixels under the white one and subtracts the sum under the
  black one. Real faces reliably produce certain values — the eye region is
  darker than the cheeks below it, the bridge of the nose is brighter than the
  eyes either side of it — so a handful of such differences already separates
  faces from most background patches.
* A **cascade** is a chain of ever-stricter stages. Stage 1 uses a couple of
  features and rejects the vast majority of image patches instantly; only the
  survivors pay for stage 2, and so on. That is why it runs in real time: almost
  no patch reaches the expensive end of the chain.
* It slides a window over the image at many scales, which is why the detector
  needs ``scaleFactor``, ``minNeighbors`` and ``minSize`` (documented below).

Its limits, so you know when to reach for something else: it only finds
*roughly frontal, roughly upright* faces, and it produces false positives on
busy textures. For anything harder, use a DNN-based detector (OpenCV's
``cv2.dnn`` face model, or MediaPipe Face Detection — already a dependency of
this repo).

Version note: OpenCV **5.0 removed ``cv2.CascadeClassifier``** along with the
rest of the legacy cascade API. This module therefore needs OpenCV 4.x, which is
what ``requirements.txt`` pins. If you upgrade, port this to
``cv2.FaceDetectorYN`` (the bundled DNN detector) or to MediaPipe.

Why this exists here: it feeds the mosaic projects, which need thousands of
small, consistently-cropped face tiles.
"""

# =====================================================================
# Import modules
# =====================================================================

# import internal modules
import argparse
from pathlib import Path
from typing import List, Optional, Tuple

# import 3rd-party modules
import cv2

# import local modules
from core.utils.image_pather import get_img_paths

# =====================================================================
# Declare constants
# =====================================================================

# Resolve the model next to THIS file rather than relative to the working
# directory, so the detector works no matter where you launch Python from.
MODELS_DIR = Path(__file__).resolve().parent / "models"
DEFAULT_CASCADE_NAME = "haarcascade_frontalface_default.xml"

# =====================================================================
# Define functions
# =====================================================================


# The annotation is a string so that it is not evaluated at import time: on
# OpenCV 5 the attribute no longer exists, and we would rather fail with the
# explanatory message below than with a bare AttributeError on import.
def load_face_cascade(cascade_path: Optional[Path] = None) -> "cv2.CascadeClassifier":
    """Load the Haar cascade, falling back to the copy bundled with OpenCV.

    OpenCV ships these XML files itself (``cv2.data.haarcascades``), so there is
    no need to fail just because the local ``models/`` folder is empty — that
    folder is git-ignored, being downloaded data rather than source.
    """
    if not hasattr(cv2, "CascadeClassifier"):
        raise RuntimeError(
            f"cv2.CascadeClassifier is not available in OpenCV {cv2.__version__}. "
            "The legacy Haar cascade API was removed in OpenCV 5. "
            "Install OpenCV 4 (pip install 'opencv-python<5'), or switch to "
            "cv2.FaceDetectorYN / MediaPipe Face Detection."
        )

    candidates: List[Path] = []

    if cascade_path is not None:
        candidates.append(Path(cascade_path))

    candidates.append(MODELS_DIR / DEFAULT_CASCADE_NAME)
    candidates.append(Path(cv2.data.haarcascades) / DEFAULT_CASCADE_NAME)

    for candidate in candidates:
        if candidate.is_file():
            cascade = cv2.CascadeClassifier(str(candidate))

            # CascadeClassifier does not raise on a malformed or unreadable XML;
            # it just stays empty and then detects nothing at all. Check it.
            if not cascade.empty():
                return cascade

    raise FileNotFoundError(
        "Could not load a face cascade. Tried: " + ", ".join(str(c) for c in candidates)
    )


def detect_face(
    input_dir: Path,
    output_dir: Path,
    bbox_width: int = 128,
    bbox_height: int = 128,
    scale_factor: float = 1.3,
    min_neighbors: int = 10,
    min_size: Tuple[int, int] = (350, 350),
    cascade_path: Optional[Path] = None,
    verbose: bool = True,
) -> int:
    """Crop every detected face out of every image in ``input_dir``.

    Arguments:
    * input_dir: folder of photos to scan (searched recursively).
    * output_dir: folder to write the face crops into. Created if missing.
    * bbox_width / bbox_height: size every crop is resized to. Keeping them
      equal (square) avoids stretching, since detected faces are square-ish.
    * scale_factor: how much the search window grows between passes. ``1.3``
      means "+30% each pass" — fast but coarse; ``1.05`` finds more faces and is
      several times slower.
    * min_neighbors: how many overlapping detections a region needs before it is
      accepted. The detector fires several times around a real face, so a high
      value (10) keeps only strong, well-supported hits and kills most false
      positives — at the cost of missing borderline faces.
    * min_size: ignore faces smaller than this, in pixels. The default is
      deliberately large because these crops feed a mosaic and small faces are
      too blurry to be useful tiles. Lower it a lot (e.g. ``(30, 30)``) for
      general-purpose detection.
    * cascade_path: use a specific cascade XML instead of the default.
    * verbose: print progress.

    Returns: the number of faces written to disk.
    """
    input_dir, output_dir = Path(input_dir), Path(output_dir)

    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory does not exist: {input_dir}")

    # create the destination once, outside the loop
    output_dir.mkdir(parents=True, exist_ok=True)

    face_cascade = load_face_cascade(cascade_path)
    img_paths = get_img_paths(input_dir)

    if verbose:
        print(f"Scanning {len(img_paths)} images from {input_dir}")

    face_count = 0

    for img_path in img_paths:
        img = cv2.imread(img_path)

        # cv2.imread returns None instead of raising on unreadable files
        if img is None:
            if verbose:
                print(f"  skipped (unreadable): {img_path}")
            continue

        # The cascade works on intensity only, so drop the colour: it is 3x less
        # data and colour carries no information this detector can use.
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Histogram equalisation spreads the brightness values over the full
        # 0-255 range. Haar features are *differences* between neighbouring
        # regions, so stretching the contrast makes those differences larger and
        # more consistent between an under-exposed and a well-lit photo.
        img_gray = cv2.equalizeHist(img_gray)

        # returns one (x, y, w, h) box per detection, in pixels
        faces = face_cascade.detectMultiScale(
            img_gray,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=min_size,
            flags=cv2.CASCADE_SCALE_IMAGE,
        )

        for (x, y, w, h) in faces:
            # Slice the *colour* image, not the grayscale one: grayscale was only
            # ever an input to the detector. NumPy slicing is [rows, columns],
            # i.e. [y, x] — the opposite order of the (x, y) the box gives us.
            roi = img[y : y + h, x : x + w]

            # Downscaling, so INTER_AREA avoids the aliasing that INTER_LINEAR
            # would introduce (see core/utils/renderer/get_resize_interpolation.py).
            out_img = cv2.resize(roi, (bbox_width, bbox_height), interpolation=cv2.INTER_AREA)

            # zero-padded counter keeps the files in creation order when sorted
            out_path = output_dir / f"face_{face_count:05d}.jpg"
            cv2.imwrite(str(out_path), out_img)

            face_count += 1

        if verbose and faces is not None and len(faces):
            print(f"  {len(faces)} face(s) in {Path(img_path).name} (total: {face_count})")

    if verbose:
        print(f"Done: {face_count} faces written to {output_dir}")

    return face_count


# =====================================================================
# Run demo
# =====================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-dir", required=True, type=Path, help="Folder of photos to scan.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Where to write the face crops.")
    parser.add_argument("--size", type=int, default=128, help="Output crop size in pixels (square).")
    parser.add_argument(
        "--min-size",
        type=int,
        default=350,
        help="Ignore faces smaller than this many pixels. Lower it for small photos.",
    )
    args = parser.parse_args()

    detect_face(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        bbox_width=args.size,
        bbox_height=args.size,
        min_size=(args.min_size, args.min_size),
    )
