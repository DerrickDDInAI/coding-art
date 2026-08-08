# coding-art

Exploring computer-vision techniques to create generative art.

An ongoing personal project, started on `Jan 19, 2021`.

## Table of Contents

- [What this is](#what-this-is)
- [Quick start](#quick-start)
- [How the repo is organised](#how-the-repo-is-organised)
- [The projects](#the-projects)
- [The shared library](#the-shared-library)
- [Data sources](#data-sources)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)

---

## What this is

A collection of self-contained experiments that each take images or video and turn
them into something else: a mosaic, a morph, a fractal, a simulation, a 3D scene.

There is no single application to run. **Each project is a Jupyter notebook**
that you open and step through, plus — where the code was worth reusing — Python
modules under [`core/utils`](core/utils).

New to computer vision? Read **[docs/cv-primer.md](docs/cv-primer.md)** first. It
covers the conventions (`BGR` vs `RGB`, `(height, width)` vs `(width, height)`,
interpolation, `uint8` overflow) that account for most of the confusing bugs in
image code. Every module in `core/utils` is commented with a beginner in mind and
is a reasonable second thing to read.

### Objectives

- Learn computer vision in general
- Explore computer-vision techniques to create art

---

## Quick start

```bash
git clone <this repo>
cd coding-art

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .          # makes `import core.utils...` work from any folder
```

Check that it worked:

```bash
pytest
```

Then open a project:

```bash
jupyter notebook core/mosaic/mosaic_images.ipynb
```

`requirements.txt` is split into sections — only the "core library" block is
mandatory, the rest is per-project and can be commented out.

### Secrets

`core/utils/scraper/pexels.py` needs a Pexels API key. Put it in a `.env` file at
the repo root (git-ignored):

```
PEXELS_API_KEY=your_key_here
```

Never hard-code a key in a source file. A key committed to a repository stays
recoverable from the history forever, so the only real remedy is to revoke it.

---

## How the repo is organised

```
coding-art
├── README.md               : this file
├── pyproject.toml          : package metadata, pytest configuration
├── requirements.txt        : packages to install
├── docs/
│   └── cv-primer.md        : the conventions every project relies on — read first
├── tests/                  : pytest suite for core/utils
│
└── core/
    ├── utils/              : the shared library (see core/utils/README.md)
    ├── assets/             : images, video, data, 3D files — git-ignored
    ├── templates/          : starting-point notebooks for a new project
    ├── sandbox/            : throwaway exploration, not maintained
    └── <one folder per project, listed below>
```

Conventions:

- **One folder per project**, holding its notebooks and any modules specific to it.
- **`scratch/` sub-folders** hold work-in-progress variants of a notebook. The
  polished version lives in the project folder itself.
- **`core/assets/` is git-ignored.** Photos, videos and models are large and
  personal, so they are not committed. Scripts create the folders they need.
- **Imports are absolute from the repo root**: `from core.utils.… import …`.

---

## The projects

| Folder | What it explores |
| --- | --- |
| [`mosaic`](core/mosaic) | Photo mosaics: rebuild an image out of thousands of smaller ones, or out of geometric shapes, text and triangles. |
| [`borders`](core/borders) | Contours, circle detection, instance segmentation — finding and drawing the outline of things. |
| [`fractals`](core/fractals) | Mandelbrot rendering; the cleanest example of pixel → number → colour. |
| [`morphing`](core/morphing) | Feature-point detection, Delaunay triangulation and affine warping to morph one image into another. |
| [`cellular_automaton`](core/cellular_automaton) | Conway's Game of Life and custom rules, JIT-compiled with numba. |
| [`voronoi`](core/voronoi) | Voronoi diagrams and Delaunay triangulation as an image style. |
| [`average_images`](core/average_images) | What a stack of photos looks like when you average it. |
| [`image_blender`](core/image_blender) | Blend modes between images. |
| [`shuffle_image`](core/shuffle_image) | Rearranging pixels: shuffling, transferring, sorting. |
| [`image_dancer`](core/image_dancer) | Driving image distortion from an audio or motion signal. |
| [`patterns`](core/patterns) | Procedural pattern generation. |
| [`superellipse`](core/superellipse) | Superellipse / squircle geometry. |
| [`image_to_sound`](core/image_to_sound) | Encode an image so that it draws itself on an audio spectrogram. |
| [`pose_estimation`](core/pose_estimation) | Body-landmark tracking, plus a particle simulation driven by it. |
| [`object_detection`](core/object_detection) | YOLOv5 through OpenCV's DNN module. |
| [`interact_real_objects`](core/interact_real_objects) | Simple augmented reality over a webcam feed. |
| [`models_3d`](core/models_3d) | Blender scripting: grease pencil, generated meshes, 3D data visualisation. |
| [`speed`](core/speed) | Benchmarking the same operation across implementations. |
| [`videostream`](core/videostream) | Live webcam processing. |

> The scripts in `models_3d` run **inside Blender** (Scripting tab, or
> `blender --python <file>.py`), not in the virtual environment — `bpy` cannot be
> pip-installed.

---

## The shared library

[`core/utils`](core/utils) holds the code that more than one project needed. It is
the tested part of the repo and the best-commented. See
[`core/utils/README.md`](core/utils/README.md) for the module list.

A typical project uses it like this:

```python
from core.utils.project_manager import Project
from core.utils.renderer.resizer import resize_with_pad
from core.utils.renderer.videographer import create_video

# create the folder layout and list the input images
project = Project(
    project_dir="core/assets/images/my_run",
    in_img_dir="source",
    out_img_dir_list=["frames"],
)

for img_path in project.in_img_path_list:
    ...  # the interesting part: write frames into out_img_dir_dict["frames"]

# stitch the frames into a video, letterboxing any odd-shaped frame
create_video(
    img_dir=project.out_img_dir_dict["frames"],
    out_path="core/assets/images/my_run/out.mp4",
    fps=25,
    out_img_shape=(1080, 1080),
    resize_fct=resize_with_pad,
)
```

---

## Data sources

- My own photo and video collection
- Public datasets, downloaded manually or scraped (see `core/utils/scraper`)

Both live under `core/assets/`, which is git-ignored.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'core'`**
Run `pip install -e .` from the repo root once. Notebooks open with their working
directory set to `core/` (see `.vscode/settings.json`), so relative asset paths
work — but that means `core` itself is not on `sys.path` without the install.

**`ImportError: ... incompatible architecture (have 'x86_64', need 'arm64')`**
An Intel build of OpenCV under an Apple Silicon Python. Reinstall it:

```bash
pip uninstall -y opencv-python && pip install --no-cache-dir opencv-python
```

**A video renders but is 0 bytes or has one frame**
Every frame must match the size given to `VideoWriter` exactly — OpenCV discards
mismatched frames without an error. Pass `out_img_shape` and a `resize_fct` to
`create_video`.

**The GIF's colours are inverted (blue sky is orange)**
BGR was written where RGB was expected. See
[docs/cv-primer.md](docs/cv-primer.md#2-opencv-uses-bgr-everybody-else-uses-rgb).

**`Could not optimize the GIF`**
`pygifsicle` needs the gifsicle binary: `brew install gifsicle`. The GIF is still
written correctly without it.

---

## Roadmap

- [x] Create repo
- [x] Clean up the structure, split the shared code into a tested library
- [x] Implement a binary search tree to speed up mosaic tile matching
- [ ] Use it in the mosaic notebooks (currently a linear scan)
- [ ] In mosaic creation: process images to better match the grid cell they replace
- [ ] Vectorise the fractal renderer with NumPy
- [ ] Prepare and scrape more source images
- [ ] Create mosaic GIFs and videos
- [ ] Create mosaic 3D models?

Continuously:

- [ ] Learn and apply new computer-vision techniques
- [ ] Create art reflecting current events

---

## Author and acknowledgment

This project is carried out by **Van Frausum Derrick**, from the Theano 2.27
promotion at BeCode.

Some projects vendor third-party code, with attribution kept in the file header:

- `core/morphing/morph.py` — András Jankovics, adapted from David Dowd's
  [Morphing](https://github.com/ddowd97/Morphing)
- `core/image_to_sound/spectrographic.py` — Levi Borodenko,
  [spectrographic](https://github.com/LeviBorodenko/spectrographic) (MIT)
- `core/image_to_sound/tuto.py` — Samuel Prevost
- `core/fractals/` — derived from
  [Real Python's Mandelbrot tutorial](https://realpython.com/mandelbrot-set-python/)
