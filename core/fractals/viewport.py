"""Map pixel coordinates to points on the complex plane (and back).

The general problem
-------------------
Every renderer has to bridge two different coordinate systems:

* **Pixel space** — integers, origin at the *top-left*, y grows **downwards**,
  bounded by the image size. This is how images are stored, in this repo and
  everywhere else.
* **World space** — real numbers, origin wherever you decide, y grows **upwards**,
  unbounded. This is where the maths lives.

Panning and zooming are nothing more than changing the mapping between the two.
Zooming in does not add pixels, it makes each pixel cover a *smaller* piece of
world space, so more detail becomes visible. This is exactly the transform behind
camera calibration and image warping — the Mandelbrot renderer is just an easy
place to see it in isolation.

The two gotchas, both handled below:

1. **The y axis flips.** Forget the minus sign and your fractal renders upside
   down. (For a symmetric shape like the Mandelbrot set you may not even notice —
   which is precisely what makes it a nasty bug.)
2. **Only the width is given.** The height is *derived* from the image's aspect
   ratio, so that a square in world space stays square on screen. Setting both
   independently is how you accidentally stretch your render.

Derived from https://realpython.com/mandelbrot-set-python/
"""

# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from dataclasses import dataclass

# import 3rd-party modules
from PIL import Image

# =====================================================================
# Define classes
# =====================================================================


@dataclass
class Viewport:
    """The rectangle of the complex plane that an image is looking at.

    Attributes:
    * image: the ``PIL.Image`` being rendered into. Its pixel size fixes the
      resolution and the aspect ratio.
    * center: the world-space point that lands in the middle of the image.
      Pan by moving it.
    * width: how much world space the image spans horizontally. Zoom by
      shrinking it — halving ``width`` doubles the magnification.

    Everything else (``height``, ``scale``, ``offset``) is derived, so the three
    attributes above can never disagree with each other.
    """

    image: Image.Image
    center: complex
    width: float

    @property
    def scale(self) -> float:
        """World-space units per pixel — the zoom level.

        Small scale = strongly zoomed in. This single number is what converts a
        pixel step into a world-space step.
        """
        return self.width / self.image.width

    @property
    def height(self) -> float:
        """World-space height, derived from the pixel aspect ratio.

        Because it reuses ``scale``, a pixel covers the same distance vertically
        as horizontally, which is what keeps circles round.
        """
        return self.scale * self.image.height

    @property
    def offset(self) -> complex:
        """World-space position of the **top-left** pixel.

        Pixel (0, 0) sits half a width to the left of the centre and half a
        height above it. In complex terms that is
        ``center + (-width + i*height) / 2`` — negative on the real (horizontal)
        axis, positive on the imaginary (vertical) axis, because in world space
        "up" is positive.
        """
        return self.center + complex(-self.width, self.height) / 2

    def __iter__(self):
        """Walk every pixel of the image, row by row.

        Row-major order (y outer, x inner) matches how images are laid out in
        memory, so it is the cache-friendly direction to iterate.
        """
        for y in range(self.image.height):
            for x in range(self.image.width):
                yield Pixel(self, x, y)


@dataclass
class Pixel:
    """One pixel, aware of the viewport it belongs to.

    Attributes:
    * viewport: the ``Viewport`` that defines this pixel's place in world space.
    * x: column index, ``0`` at the left.
    * y: row index, ``0`` at the top.

    ``color`` is a property with a getter and a setter, so reading and writing a
    pixel both look like plain attribute access.
    """

    viewport: Viewport
    x: int
    y: int

    @property
    def color(self):
        """Read this pixel's colour from the underlying image."""
        return self.viewport.image.getpixel((self.x, self.y))

    @color.setter
    def color(self, value) -> None:
        """Write this pixel's colour into the underlying image."""
        self.viewport.image.putpixel((self.x, self.y), value)

    def __complex__(self) -> complex:
        """Allow ``complex(pixel)`` — the pixel's position in world space.

        Three steps in one expression:
        1. ``complex(self.x, -self.y)`` — treat the pixel coordinates as a
           complex number, **negating y** to flip the downward image axis into
           the upward world axis.
        2. ``* scale`` — convert from pixels to world-space units (zoom).
        3. ``+ offset`` — shift so pixel (0, 0) lands on the top-left corner of
           the viewport rather than on the world origin (pan).
        """
        return complex(self.x, -self.y) * self.viewport.scale + self.viewport.offset
