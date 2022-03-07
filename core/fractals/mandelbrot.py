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
from math import log

# import 3rd-party modules

# import local modules


# =====================================================================
# Define classes
# =====================================================================

@dataclass
class MandelbrotSet:
    """
    dataclass to define a Mandelbrot set

    Attributes:
    * escape_radius: the math formula below to smooth out banding artifacts
    is based on the assumption that the escape radius approaches infinity, so it can't be hardcoded anymore.
    """
    max_iterations: int
    escape_radius: float = 2.0

    # def __contains__(self, c: complex) -> bool:
    #     """
    #     Special method to allow to leverage the use of in and not in operator.

    #     Logic:
    #     checks if a candidate value (complex number c) is stable:
    #     stable if the magnitude Zn resulting from the recursive formula exceeds the radius of 2 after n iterations
    #     This recursive formula gives the Mandelbrot sequence.

    #     The absolute value of a complex number, a+bi (also called the modulus) is defined as the distance between the origin (0,0) and the point (a,b) in the complex plane.

    #     By default z = 0 as in a mandelbrot sequence, the first element is always 0

    #     Note: this function works on individual numbers rather than a whole matrix
    #     """
    #     # in mandelbrot sequence, the first element is always 0
    #     z = 0

    #     # compute sequence over n iterations
    #     for _ in range(self.max_iterations):
    #         z = z ** 2 + c

    #         # if radius of z exceeds 2, return false (i.e breaking the loop as soon as magnitude of z exceeds threshold)
    #         if abs(z) > 2:
    #             return False

    #     # return true if after max iterations, radius of z hasn't exceeded 2
    #     return True

    def __contains__(self, c: complex) -> bool:
        """
        Special method to allow to leverage the use of in and not in operator

        Logic:
        Candidate value is considered stable if stability equals to 1, 
        i.e the sequence didn't diverge after max number of iterations

        Note: here, the iterative approach to test the stability of a given point is actually an approximation of the actual Mandelbrot set.
        As for some points, more iterations than the given maximum number of iterations could be required to know if they're stable or not, which may not be feasible in practice.

        """
        return self.stability(c) == 1

    def escape_count(self, c: complex, smooth=False) -> Union[int,float]:
        """
        Function to get the escape count, i.e the number of iterations it takes to detect divergence

        Arguments:
        * smooth: boolean value to decide to return fractional escape count 
        => to get rid of color banding outside the Mandelbrot set (happening due to discrete escape count).
        -> by interpolating the intermediate escape count

        """
        # in mandelbrot sequence, the first element is always 0
        z = 0
        
        # compute sequence over n iterations
        for iteration_nb in range(self.max_iterations):
            z = z ** 2 + c

            # if radius of z exceeds a given radius, return number of iterations (i.e breaking the loop as soon as magnitude of z exceeds threshold)
            if abs(z) > self.escape_radius:

                if smooth:
                    return iteration_nb + 1 - log(log(abs(z))) / log(2)
                return iteration_nb
        
        # return max iterations if after max number of iterations, radius of z hasn't exceeded 2
        return self.max_iterations

    def stability(self, c: complex, smooth=False, clamp=True) -> float:
        """
        Function to get a stability metric: ratio of escape count to max number of iterations
        Arguments:
        * clamp: boolean to clamp the stability value
        Needed when smoothing is activated:
        escape count greater than 1 or negative can happen, 
        leading to pixel intensities wrapping around the maximum and minimum levels allowed
        """
        value = self.escape_count(c, smooth) / self.max_iterations

        return max(0.0, min(value, 1.0)) if clamp else value