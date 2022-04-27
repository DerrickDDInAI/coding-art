"""
Local module that defines the particles
"""

# =====================================================================
# Import modules
# =====================================================================

# Import internal modules
import math
from typing import List, Set, Dict, TypedDict, Tuple, Optional


# =====================================================================
# Define classes
# =====================================================================

class Particle:
    """
    Particle is represented by a circle object.
    At the initialization, it has 9 attributes:
    * name: particle's name
    * x_px: particle's pixel position in the x direction (at the circle center)
    * y_px: particle's pixel position in the y direction (at the circle center)
    * size_px: particle's circle radius in pixel
    * mass: particle's mass
    * color: particle's circle color
    * speed: particle's speed
    * angle: particle's direction
    * elasticity: particle's elasticity.

    """

    def __init__(
        self,
        name: str,
        xy_position_px: Tuple[float],
        size_px: int = 50,
        mass: int = 1,
        color: Tuple[int] = (0, 0, 255),  # RGB color code for blue
        thickness: int = -1 
    ) -> None:
        """
        Function to create an instance of Particle class.
        Particle instance is created with no velocity (speed and angle);
        and an elasticity to determine the level of elastic collision 
        between him and another object. 
        """
        self.name: str = name
        self.x_px: float
        self.y_px: float
        self.x_px, self.y_px = xy_position_px
        self.size_px: int = size_px
        self.mass: int = mass
        self.color: Tuple[int] = color
        self.thickness: int = thickness

        self.speed: float = 0.0  # particle starts with no speed
        self.angle: float = 0.0  # particle has no direction yet
        self.elasticity: float = 0.9

    def __repr__(self) -> str:
        """
        Function to print the Particle instance in the specified format.
        """
        return f"{self.name}"

    def move(self) -> None:
        """
        Function to update the particle's position due to its speed and angle.
        """
        self.x_px += math.sin(self.angle) * self.speed
        self.y_px -= math.cos(self.angle) * self.speed