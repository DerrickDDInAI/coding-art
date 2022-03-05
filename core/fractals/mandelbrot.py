from dataclasses import dataclass

"""
Program to define a class for Mandelbrot sets
"""

# =====================================================================
# Import modules
# =====================================================================

# import internal modules
# from typing import List, Set, Dict, TypedDict, Tuple, Optional, Union
from dataclasses import dataclass

# import 3rd-party modules

# import local modules


# =====================================================================
# Define classes
# =====================================================================

@dataclass
class MandelbrotSet:
    max_iterations: int

    def __contains__(self, c: complex) -> bool:
        """
        Special method to allow to leverage the use of in and not in operator.

        Logic:
        checks if a candidate value (complex number c) is stable:
        stable if the magnitude Zn resulting from the recursive formula exceeds the radius of 2 after n iterations
        This recursive formula gives the Mandelbrot sequence.

        The absolute value of a complex number, a+bi (also called the modulus) is defined as the distance between the origin (0,0) and the point (a,b) in the complex plane.

        By default z = 0 as in a mandelbrot sequence, the first element is always 0

        Note: this function works on individual numbers rather than a whole matrix
        """
        # in mandelbrot sequence, the first element is always 0
        z = 0

        # compute sequence over n iterations
        for _ in range(self.max_iterations):
            z = z ** 2 + c

            # if radius of z exceeds 2, return false (i.e breaking the loop as soon as magnitude of z exceeds threshold)
            if abs(z) > 2:
                return False

        # return true if after max iterations, radius of z hasn't exceeded 2
        return True