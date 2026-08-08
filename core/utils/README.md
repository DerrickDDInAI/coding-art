# `core/utils` — the shared library

Everything here is imported by the project notebooks. It is the only part of the
repo that is tested (`pytest` from the repo root) and the best place to start
reading, because the same handful of ideas reappear in every project.

Import paths are always absolute from the repo root:

```python
from core.utils.project_manager import Project
from core.utils.renderer.resizer import resize_with_pad
```

If that raises `ModuleNotFoundError`, install the repo in editable mode once:

```bash
pip install -e .
```

## Modules

| Module | What it does |
| --- | --- |
| `image_pather.py` | Collect image paths from a folder, in a deliberate order. |
| `project_manager.py` | `Project` — create a run's folder layout and list its inputs. |
| `binary_search_tree.py` | Map a brightness value to an image path; nearest-match lookup for mosaics. |
| `renderer/get_resize_interpolation.py` | Choose `INTER_AREA` vs `INTER_CUBIC` for a resize. |
| `renderer/resizer.py` | Change an image's shape without distorting it (pad or crop). |
| `renderer/frame_sequence.py` | Shared plumbing: collect, order, resize and hold frames. |
| `renderer/videographer.py` | `create_video` — folder of images → MP4. |
| `renderer/giffer.py` | `create_gif` — folder of images → animated GIF. |
| `face_detector/face_detector.py` | Haar-cascade face detection; produces mosaic tiles. |
| `scraper/pexels.py` | Download images from pexels.com (needs `PEXELS_API_KEY`). |

## Notebooks in this folder

`bg_removal/`, `color_detector/`, `image_similarity_measurer/` and
`renderer/*.ipynb` are exploratory notebooks, not importable modules. They are
where a technique gets tried out before it is worth extracting into a module.

## Conventions

- **Shapes are `(height, width)`**, NumPy order, everywhere in this package. The
  flip to OpenCV's `(width, height)` happens at the call site and is commented.
- **Reads are checked.** `cv2.imread` returns `None` instead of raising, so every
  read here raises `FileNotFoundError` immediately rather than letting a `None`
  travel down the pipeline.
- **No mutable default arguments.** Python evaluates defaults once, so a
  `list = []` default is shared between calls and leaks state between renders.
- **Frames stream, they are not collected.** `iter_frames` is a generator: a
  1000-frame 4K sequence would be ~25 GB in a list, but a writer only ever needs
  one frame at a time.

## Planned modules

These were placeholder files with no implementation and have been removed. The
ideas are still on the roadmap:

- **clusterer** — group images by visual similarity.
- **histogramer** — histogram matching / specification between images.
- **image_editor**, **screenshooter**, **snapper** — capture and editing helpers.
- **image_mapper** — best-matching image or pixel for a region of interest
  (currently done inline in the mosaic notebooks).

Write them when a notebook actually needs them, not before.
