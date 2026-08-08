"""The Mandelbrot set: deciding whether one point of the plane is "inside" it.

The idea in one paragraph
------------------------
Take a point ``c`` on the plane and read it as a complex number. Start at
``z = 0`` and repeat ``z = z**2 + c`` over and over. For some values of ``c``,
``z`` stays small forever; for others it shoots off to infinity. The Mandelbrot
set is simply *the set of points that stay small*. Its famous shape is not drawn
by any formula — it falls out of running that one line of arithmetic on every
pixel.

Why this belongs in a computer-vision repo
------------------------------------------
It is the cleanest possible example of the pattern behind every project here:
**map each pixel to a number, then map that number to a colour.** Change the
mapping and you change the image. Everything downstream — colour maps, contrast
curves, anti-aliasing — behaves exactly as it does on a photograph.

Two practical tricks are implemented below, and both are general image-processing
techniques rather than fractal trivia:

* **The escape radius.** Once ``|z| > 2`` the sequence provably diverges, so we
  can stop early instead of iterating forever. A larger radius costs a little
  more work but makes the smoothing below more accurate.
* **Smoothing (fractional escape counts).** The raw iteration count is a whole
  number, so colouring by it produces visible concentric rings — *colour
  banding*, the same artefact you see in a low-bit-depth photo gradient. The
  logarithm below interpolates *between* iteration counts and turns those steps
  into a continuous gradient. This is the same problem, and the same class of
  fix, as dithering a photograph.

Derived from https://realpython.com/mandelbrot-set-python/

ToDo: vectorise with NumPy — iterating in pure Python costs one interpreter loop
per pixel per iteration, which is the reason a large render takes minutes.
``core/fractals/create_fractals.ipynb`` shows the array-based version.
"""

# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from dataclasses import dataclass
from math import log
from typing import Union

# =====================================================================
# Define classes
# =====================================================================


@dataclass
class MandelbrotSet:
    """The Mandelbrot set, sampled at a given precision.

    Attributes:
    * max_iterations: how many times to apply ``z = z**2 + c`` before declaring a
      point "stable". This is the quality/speed dial: higher values reveal more
      detail along the boundary but cost proportionally more time. Note this
      makes every render an *approximation* — a point that would escape on
      iteration 5 000 is indistinguishable from one that never escapes when you
      stop at 100.
    * escape_radius: the magnitude above which we call the sequence divergent.
      Mathematically 2.0 is enough, but the smoothing formula in
      :meth:`escape_count` assumes an escape radius approaching infinity, so
      raising it (100, 1000) makes the smooth gradient noticeably cleaner.
    """

    max_iterations: int
    escape_radius: float = 2.0

    def __contains__(self, c: complex) -> bool:
        """Allow ``c in mandelbrot_set``.

        Implementing ``__contains__`` is what makes the ``in`` operator work on a
        custom class. A point is "in" the set when it never escaped, i.e. when
        its stability is exactly 1.
        """
        return self.stability(c) == 1

    def escape_count(self, c: complex, smooth: bool = False) -> Union[int, float]:
        """Number of iterations it took for ``c`` to diverge.

        Returns ``max_iterations`` if it never did.

        Arguments:
        * smooth: return a *fractional* count instead of a whole number, which
          removes the colour banding described in the module docstring.

        The smoothing formula, unpacked: when the sequence escapes we know it
        crossed the radius *somewhere between* the previous iteration and this
        one. Because ``z`` is being squared each step, its magnitude grows
        doubly-exponentially, so ``log(log(|z|)) / log(2)`` recovers roughly how
        far past the threshold we overshot — and subtracting it interpolates the
        count back to where the crossing actually happened.
        """
        # every Mandelbrot sequence starts at zero, by definition
        z = 0

        for iteration_nb in range(self.max_iterations):
            z = z**2 + c

            # abs() of a complex number is its distance from the origin
            if abs(z) > self.escape_radius:
                if smooth:
                    return iteration_nb + 1 - log(log(abs(z))) / log(2)
                return iteration_nb

        # survived every iteration: treat it as a member of the set
        return self.max_iterations

    def stability(self, c: complex, smooth: bool = False, clamp: bool = True) -> float:
        """Escape count rescaled to ``0.0 - 1.0``, ready to be turned into a colour.

        ``0.0`` means "escaped immediately" (far outside the set) and ``1.0``
        means "never escaped" (inside the set). Normalising here means the
        colouring code never has to know ``max_iterations``.

        Arguments:
        * clamp: force the result into ``[0, 1]``. The smoothing correction can
          push a value slightly below 0 or above 1, and feeding that to a colour
          map makes the intensity *wrap around* — a black pixel suddenly renders
          white, producing bright speckles along the boundary.
        """
        value = self.escape_count(c, smooth) / self.max_iterations

        return max(0.0, min(value, 1.0)) if clamp else value
