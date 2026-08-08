"""Collect image file paths from a folder.

Why a whole module for this?
----------------------------
Almost every computer-vision script in this repo starts the same way: "give me
the list of images to work on". Doing that inline every time leads to subtle
differences (one script forgets `.JPEG`, another forgets to sort) which makes
results impossible to reproduce. Centralising it here means every project reads
its inputs in exactly the same, predictable order.

A note on ordering
------------------
Ordering matters a lot in this repo. When you turn a folder of frames into a
video or a GIF, the *file order is the time axis*. `Path.glob()` returns files in
whatever order the filesystem hands them over, which is not guaranteed to be
alphabetical, so we sort by default. If your frames are named `frame_1.png` ...
`frame_10.png`, alphabetical sorting gives 1, 10, 2, 3 — pad the numbers when you
save them (`frame_0001.png`) and sorting becomes chronological.
"""

# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from pathlib import Path
from random import shuffle as shuffle_in_place
from typing import Iterable, List, Optional, Union

# =====================================================================
# Declare constants
# =====================================================================

# Extensions we consider to be "an image".
# Suffix comparison in pathlib is case-sensitive, so a file called `PHOTO.JPG`
# has the suffix `.JPG` and would be missed if we only listed lowercase forms.
# We normalise to lowercase when comparing instead of listing every variant.
IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"})

# =====================================================================
# Define functions
# =====================================================================


def get_img_paths(
    input_dir: Union[str, Path],
    extensions: Iterable[str] = IMAGE_EXTENSIONS,
    to_shuffle: bool = False,
    recursive: bool = True,
    sort: bool = True,
    limit: Optional[int] = None,
) -> List[str]:
    """Return the paths of every image found in ``input_dir``.

    Arguments:
    * input_dir: folder to search, as a string or a ``Path``.
    * extensions: which file suffixes count as images. Case is ignored.
    * to_shuffle: return the paths in random order (useful for mosaics, where a
      deterministic order would make the tile pattern visibly repetitive).
    * recursive: also search sub-folders. Turn this off when a folder contains
      nested "output" directories you do not want to feed back into the input.
    * sort: sort alphabetically. Ignored when ``to_shuffle`` is True, because the
      two options contradict each other.
    * limit: keep at most this many paths. Handy to smoke-test a slow pipeline on
      20 images before launching it on 20 000.

    Returns: a list of paths as strings, because ``cv2.imread`` does not accept
    ``Path`` objects on every OpenCV version.
    """
    # accept a plain string as well as a Path, so callers do not have to care
    input_dir = Path(input_dir)

    # fail loudly and early: an empty result caused by a typo in the folder name
    # is much harder to debug three pipeline steps later
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input image directory does not exist: {input_dir}")

    # normalise the extensions once so the comparison below is a cheap set lookup
    wanted_suffixes = {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions}

    # "**/*" walks into sub-folders, "*" stays in the top folder only
    glob_pattern = "**/*" if recursive else "*"

    img_paths = [
        str(path)
        for path in input_dir.glob(glob_pattern)
        if path.is_file() and path.suffix.lower() in wanted_suffixes
    ]

    if to_shuffle:
        # shuffles the list in place (returns None), hence no assignment here
        shuffle_in_place(img_paths)
    elif sort:
        img_paths.sort()

    if limit is not None:
        img_paths = img_paths[:limit]

    return img_paths
