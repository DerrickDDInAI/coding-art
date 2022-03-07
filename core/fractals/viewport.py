"""
Program to define a class for Mandelbrot sets

Sources: 
- derived from https://realpython.com/mandelbrot-set-python/

ToDo: speed up execution by using numpy
"""

# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from typing import List, Set, Dict, TypedDict, Tuple, Optional, Union
from dataclasses import dataclass

# import 3rd-party modules
from PIL import Image

# import local modules


# =====================================================================
# Define classes
# =====================================================================

@dataclass
class Viewport:
    """
    Dataclass to define a viewport to pan and zoom in a certain area

    Attributes:
    * image: an Image instance
    * center: a center point expressed as a complex number
    * width: a horizontal span of world coordinates. 
    
    It also derives a handful of read-only properties from those three parameters.
    """
    image: Image.Image
    center: complex
    width: float

    @property
    def height(self):
        return self.scale * self.image.height

    @property
    def offset(self):
        return self.center + complex(-self.width, self.height) / 2

    @property
    def scale(self):
        return self.width / self.image.width

    def __iter__(self):
        """
        Special method to make iteration possible
        """
        for y in range(self.image.height):
            for x in range(self.image.width):
                yield Pixel(self, x, y)


@dataclass
class Pixel:
    """
    Dataclass to define a viewport to pan and zoom in a certain area

    Attributes:
    * viewport: a Viewport instance
    * x: x coordinate
    * y: y coordinate

    1 property color: comprises a getter and a setter for the pixel color
    """
    viewport: Viewport
    x: int
    y: int

    @property
    def color(self):
        return self.viewport.image.getpixel((self.x, self.y))

    @color.setter
    def color(self, value):
        self.viewport.image.putpixel((self.x, self.y), value)

    def __complex__(self):
        """
        Special method to cast pixel into a relevant complex number in world units:

        It flips the pixel coordinates along the vertical axis, converts them to a complex number, and then takes advantage of complex-numbers arithmetic in order to scale and move them.
        """
        return (
                complex(self.x, -self.y)
                * self.viewport.scale
                + self.viewport.offset
        )