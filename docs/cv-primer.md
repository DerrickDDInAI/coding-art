# A computer-vision primer for this repo

Read this once before opening the notebooks. It covers the handful of conventions
that every project here relies on. Almost every confusing bug in image code comes
from one of these, so they are worth twenty minutes.

---

## 1. An image is a NumPy array

When you call `cv2.imread("photo.jpg")` you get back a plain NumPy array:

```python
img = cv2.imread("photo.jpg")
img.shape   # (1080, 1920, 3)  ->  height, width, channels
img.dtype   # uint8            ->  every value is an integer 0-255
```

Three things follow from that, and they explain most of the code in this repo:

- **Indexing is `[row, column]`, i.e. `[y, x]`.** This is the opposite order from
  the `(x, y)` you use when *drawing*. `img[100, 50]` is the pixel 100 rows down
  and 50 columns across.
- **Slicing is free.** `img[y:y+h, x:x+w]` crops a region without copying any
  data — it is a *view* into the original array. Very fast, but writing to a view
  writes into the original image, which is occasionally a nasty surprise. Call
  `.copy()` when you want to be safe.
- **Anything NumPy can do to an array, you can do to an image.** `img * 0.5`
  darkens it, `255 - img` inverts it, `img.mean(axis=2)` converts it to
  grayscale. Whole-array ("vectorised") operations run in optimised C, so they
  are typically 50-100x faster than a Python `for` loop over pixels.

### The `uint8` trap

`uint8` values wrap around instead of saturating:

```python
np.uint8(250) + np.uint8(10)   # 4, not 260
```

So a "brighten" that adds 10 to every pixel turns the brightest highlights black.
Either use `cv2.add`, which saturates at 255, or convert to a float, do the maths,
clip, and convert back:

```python
out = np.clip(img.astype(np.float32) * 1.2, 0, 255).astype(np.uint8)
```

---

## 2. OpenCV uses BGR, everybody else uses RGB

`cv2.imread` returns channels in **blue, green, red** order — a historical quirk
of the library. Matplotlib, PIL and imageio all expect **RGB**. Show an OpenCV
image with matplotlib without converting, and every blue sky turns orange:

```python
plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))   # correct
```

In this repo that conversion lives in
[`core/utils/renderer/giffer.py`](../core/utils/renderer/giffer.py) — GIFs are
written through imageio, so they need it. Videos go through `cv2.VideoWriter`,
which wants BGR, so they do **not**.

### Other colour spaces worth knowing

- **HSV** (hue, saturation, value) separates *which colour* from *how bright*.
  Selecting "everything reddish regardless of lighting" is one threshold in HSV
  and nearly impossible in RGB.
- **LAB** is designed so that the numeric distance between two colours matches
  how different they look to a human eye. That makes it the right space for
  "find the tile whose colour is closest to this patch" — which is exactly what
  the mosaic projects do, and why `resize_with_pad` accepts a `cvt_color`
  argument.

---

## 3. `(height, width)` vs `(width, height)`

The single most common source of silently wrong output:

| Thing | Order |
| --- | --- |
| `img.shape` | `(height, width, channels)` |
| `cv2.resize(img, size)` | `size` is `(width, height)` |
| `cv2.VideoWriter(..., frameSize=...)` | `(width, height)` |
| NumPy indexing `img[a, b]` | `(y, x)` = `(row, column)` |
| `cv2.circle(img, center, ...)` | `center` is `(x, y)` |

The convention in this repo: **every function in `core/utils` speaks NumPy order,
`(height, width)`**, and flips to the cv2 order only at the moment it calls into
OpenCV. Each flip has a comment on it.

Getting it wrong on a *square* image produces no visible error at all, which is
how these bugs survive for months.

---

## 4. Resizing: pick the right interpolation

Resizing has to invent output pixels from input pixels. The rule to remember:

- **Shrinking → `cv2.INTER_AREA`.** It averages every source pixel that falls
  inside an output pixel, so nothing is skipped. Any other method samples a few
  pixels and misses the rest, producing *aliasing* — shimmering, jagged edges.
- **Enlarging → `cv2.INTER_CUBIC`.** Fits a smooth surface through a 4x4
  neighbourhood. `INTER_LINEAR` is faster and slightly blurrier.
- **Label images (segmentation masks) → `cv2.INTER_NEAREST`, always.** Averaging
  label 3 and label 5 into 4 invents a class that was never in the image.

[`core/utils/renderer/get_resize_interpolation.py`](../core/utils/renderer/get_resize_interpolation.py)
picks this for you.

### Aspect ratio

A video or GIF has exactly one frame size, so mixed-shape inputs must be
normalised. There are only two honest ways to do it, both in
[`core/utils/renderer/resizer.py`](../core/utils/renderer/resizer.py):

- `resize_with_pad` — keep the whole image, add black bars (letterboxing).
- `resize_with_crop` — fill the frame, throw away the overflow.

Plain `cv2.resize` to a different aspect ratio is the third option, and it
stretches faces. Avoid it unless the distortion is the effect you want.

---

## 5. Frame order is the time axis

When you turn a folder of images into a video, **the file order is the playback
order**. `Path.glob()` returns files in filesystem order, which is not
necessarily alphabetical, so `core/utils` sorts by default.

Watch out for the numbering trap: sorted alphabetically,
`frame_10.png` comes before `frame_2.png`. Zero-pad when you save
(`frame_0002.png`) and alphabetical order becomes chronological order.

---

## 6. `cv2.imread` never raises

If the file is missing, corrupt, or in an unsupported format, `cv2.imread`
returns `None` — quietly. The crash then happens somewhere else entirely, as
`AttributeError: 'NoneType' object has no attribute 'shape'`. Every read in
`core/utils` is checked immediately for exactly this reason. The same applies to
`cv2.CascadeClassifier`, which returns an *empty* classifier that detects nothing
rather than reporting the bad path.

---

## 7. Speed: vectorise, then JIT

Order of preference when a render is too slow:

1. **Replace the pixel loop with array operations.** Usually a 50-100x win, and
   no new dependency.
2. **Use the right OpenCV function.** `cv2.filter2D`, `cv2.remap`, `cv2.LUT` are
   all heavily optimised C.
3. **Reach for `numba`'s `@njit`** when the algorithm genuinely cannot be
   vectorised — cellular automata and particle simulations, where step *n+1*
   depends on step *n*. This is what `core/cellular_automaton` and
   `core/pose_estimation/play_with_particles` do.
4. **Change the algorithm.** The mosaic matcher is the example: comparing every
   patch against every tile is O(patches x tiles), while indexing the tiles in a
   tree first makes each lookup O(log tiles). See
   [`core/utils/binary_search_tree.py`](../core/utils/binary_search_tree.py).

---

## Where to start reading

| If you want to understand... | Read |
| --- | --- |
| The basic array/colour/resize conventions | `core/utils/renderer/` |
| Feature detection and triangulation | `core/morphing/morph.py` |
| Classic object detection (Haar cascades) | `core/utils/face_detector/face_detector.py` |
| Pixel → number → colour pipelines | `core/fractals/` |
| Contours and shape analysis | `core/borders/` |
| Nearest-neighbour matching at scale | `core/mosaic/` + `core/utils/binary_search_tree.py` |
