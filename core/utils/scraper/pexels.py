"""Download images from pexels.com through its public API.

Why scrape at all? Several projects here (mosaics in particular) need thousands
of images to use as tiles. Pexels publishes freely usable photos and offers a
paged search API, which makes it a convenient source.

Getting an API key
------------------
1. Sign up: https://www.pexels.com/join/
2. Request a key: https://www.pexels.com/api/ (no URL needed, confirm the email)
3. Read it back any time at https://www.pexels.com/api/new/

**Never paste the key into this file.** Put it in the repo's ``.env`` instead::

    PEXELS_API_KEY=your_key_here

``.env`` is git-ignored, so the key stays on your machine. A key committed to a
repository is exposed for good — rewriting history does not remove it from
clones or forks, so the only real fix is to revoke it and issue a new one.

Source of the original approach:
https://www.learnpythonwithrune.org/from-zero-to-creating-photo-mosaic-using-faces-with-opencv/
"""

# =====================================================================
# Import modules
# =====================================================================

# import internal modules
import argparse
import os
from pathlib import Path
from typing import Optional

# import 3rd-party modules
import requests
from pexels_api import API

# =====================================================================
# Declare constants
# =====================================================================

# repo root = three levels up from core/utils/scraper/pexels.py
REPO_ROOT = Path(__file__).resolve().parents[3]

# default download location; git-ignored, since it holds downloaded data
DEFAULT_IMG_DIR = REPO_ROOT / "core" / "assets" / "images" / "pexels"

# how long to wait for one image before giving up, in seconds. Without a timeout
# a single stalled connection can hang the whole scrape indefinitely.
REQUEST_TIMEOUT_S = 30

# =====================================================================
# Define functions
# =====================================================================


def get_api_key(env_var: str = "PEXELS_API_KEY") -> str:
    """Read the API key from the environment, with a helpful error if it is missing."""
    api_key = os.environ.get(env_var)

    if not api_key:
        raise RuntimeError(
            f"{env_var} is not set. Add it to the .env file at the repo root "
            f"(and load it, e.g. with `python-dotenv`), or export it in your shell."
        )

    return api_key


def scrape(
    api_key: str,
    query: str,
    max_imgs_count: int,
    img_dir: Optional[Path] = None,
    verbose: bool = True,
) -> int:
    """Download up to ``max_imgs_count`` photos matching ``query``.

    Arguments:
    * api_key: your Pexels key (see the module docstring).
    * query: the search term, e.g. ``"diversity"``. Also used as the sub-folder name.
    * max_imgs_count: stop after this many images.
    * img_dir: destination folder. Defaults to ``core/assets/images/pexels/<query>``.
    * verbose: print progress.

    Returns: the number of images actually written to disk.

    The API is paged: ``api.search`` fetches the first page, and
    ``api.search_next_page`` walks forward. We stop on any of three conditions —
    the requested count is reached, a page comes back empty, or there is no next
    page — because forgetting one of them is how you end up with an infinite loop.
    """
    img_dir = Path(img_dir) if img_dir is not None else (DEFAULT_IMG_DIR / query)
    img_dir.mkdir(parents=True, exist_ok=True)

    api = API(api_key)
    api.search(query)

    if verbose:
        print(f"Search: {query}")
        print(f"Total search results: {api.total_results}")
        print(f"Fetching at most {max_imgs_count} images into {img_dir}")

    downloaded_count = 0

    while downloaded_count < max_imgs_count:
        imgs = api.get_entries()

        # an empty page means the result set is exhausted
        if not imgs:
            break

        for img in imgs:
            # keep the original extension so the file stays readable
            extension = img.original.split(".")[-1]

            # photographer name + zero-padded counter: unique, sorted, and it
            # preserves the attribution the licence asks for
            img_path = img_dir / f"{img.photographer}_{downloaded_count:05d}.{extension}"

            try:
                img_request = requests.get(img.original, timeout=REQUEST_TIMEOUT_S)
            except requests.RequestException as error:
                # one bad download should not abort a scrape of thousands
                if verbose:
                    print(f"  failed: {img.original} ({error})")
                continue

            # only 200 means we actually received the image bytes
            if img_request.status_code != 200:
                if verbose:
                    print(f"  failed: {img.original} (HTTP {img_request.status_code})")
                continue

            # 'wb' = write binary: image bytes, not text
            img_path.write_bytes(img_request.content)

            downloaded_count += 1

            if verbose:
                print(f"  [{downloaded_count}/{max_imgs_count}] {img_path.name}")

            if downloaded_count >= max_imgs_count:
                break

        if not api.has_next_page:
            if verbose:
                print(f"Reached the last page: {api.page}")
            break

        api.search_next_page()

    if verbose:
        print(f"Done: {downloaded_count} images in {img_dir}")

    return downloaded_count


# =====================================================================
# Run demo
# =====================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download images from pexels.com.")
    parser.add_argument("--query", required=True, help="Search term, e.g. 'diversity'.")
    parser.add_argument("--max-imgs", type=int, default=200, help="Maximum number of images to download.")
    parser.add_argument("--img-dir", type=Path, default=None, help="Destination folder.")
    args = parser.parse_args()

    scrape(
        api_key=get_api_key(),
        query=args.query,
        max_imgs_count=args.max_imgs,
        img_dir=args.img_dir,
    )
