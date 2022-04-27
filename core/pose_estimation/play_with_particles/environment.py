"""
Local module that defines the Environment class
"""
# =====================================================================
# Import
# =====================================================================

# Import internal modules
import math
from typing import List, Set, Dict, TypedDict, Tuple, Optional


# =====================================================================
# Classes
# =====================================================================

class Environment:
    """
    Environment defines the physics and boundaries of the game.
    At the initialization, it has 7 attributes:
    * width_px: environment width in pixel
    * height_px: environment height in pixel
    * color: environment color
    * air_mass: mass of the air to add air resistance
    * elasticity: elasticity of the environment boundaries
    * gravity: gravity direction and magnitude.
    """

    def __init__(self, size_px: Tuple[int], color: Tuple[int] = (255, 255, 255)) -> None:
        self.width_px: int
        self.height_px: int
        self.width_px, self.height_px = size_px
        # self.color: Tuple[int] = color
        self.air_mass: float = 0.02
        self.elasticity: float = 0.75
        # math.pi sets gravtity direction pointing downward
        self.gravity: Tuple[float] = (math.pi, 0.01)

    def add_vectors(self, vector_1, vector_2) -> Tuple[float]:
        """
        Function to add 2 vectors.
        A vector has a magnitude and a direction.

        Returns: sum of vector_1 and vector_2
        """
        angle_1: float
        angle_2: float
        magnitude_1: float
        magnitude_2: float

        angle_1, magnitude_1 = vector_1
        angle_2, magnitude_2 = vector_2
        x = math.sin(angle_1) * magnitude_1 + math.sin(angle_2) * magnitude_2
        y = math.cos(angle_1) * magnitude_1 + math.cos(angle_2) * magnitude_2

        angle: float = 0.5 * math.pi - math.atan2(y, x)
        magnitude: float = math.hypot(x, y)

        return (angle, magnitude)

    def add_air_resistance(self, particle) -> None:
        """
        Function to make the particle (or any of its child instance classes)
        experience air resistance.
        This air resistance slows its speed.
        """
        particle.speed *= (particle.mass/(particle.mass +
                                      self.air_mass)) ** particle.size_px

    def accelerate(self, particle, vector: Tuple[float]) -> None:
        """
        Function to accelerate (= change speed and/or angle)
        the particle (or any of its child instance classes)
        by adding a vector.
        """
        particle.angle, particle.speed = self.add_vectors(
            (particle.angle, particle.speed), vector)

    def attraction(self, particle_1, particle_2) -> Optional[bool]:
        """
        Function to change the velocity (= speed and direction)
        due to gravitational attraction between 2 particles
        (or any of its child instance classes)

        Returns: None or True if particle.
        """
        # Get the distances in the x direction and in the y direction
        distance_x: float = particle_1.x_px - particle_2.x_px
        distance_y: float = particle_1.y_px - particle_2.y_px

        # Compute the distance between the 2 particles
        distance: float = math.hypot(distance_x, distance_y)

        # If distance < sum of particles' radius, it means collision;
        # No attraction effect anymore
        if distance < particle_1.size_px + particle_2.size_px:
            return True

        # Use Newton's law of universal gravitation
        theta: float = math.atan2(distance_y, distance_x)
        force: float = 0.1 * particle_1.mass * particle_2.mass / distance**2
        self.accelerate(particle_1, (theta - 0.5 * math.pi, force/particle_1.mass))
        self.accelerate(particle_2, (theta + 0.5 * math.pi, force/particle_2.mass))

    def collide(self, particle_1, particle_2, apply: bool) -> Optional[bool]:
        """
        Function to check if collision between 2 particles
        and if collision and apply is True, make them bounce.

        Returns: None or True if collision.
        """
        # Get the distances in the x direction and in the y direction
        distance_x: float = particle_1.x_px - particle_2.x_px
        distance_y: float = particle_1.y_px - particle_2.y_px

        # Compute the distance between the 2 particles
        distance: float = math.hypot(distance_x, distance_y)

        # If distance < sum of particles' radius, it means collision
        if distance < particle_1.size_px + particle_2.size_px:
            if apply:
                angle: float = math.atan2(
                    distance_y, distance_x) + 0.5 * math.pi
                total_mass: int = particle_1.mass + particle_2.mass

                particle_1_vector_a = (
                    particle_1.angle, particle_1.speed * (particle_1.mass - particle_2.mass) / total_mass)
                particle_1_vector_b = (
                    angle, 2 * particle_2.speed * particle_2.mass / total_mass)
                particle_1.angle, particle_1.speed = self.add_vectors(
                    particle_1_vector_a, particle_1_vector_b)

                particle_2_vector_a = (
                    particle_2.angle, particle_2.speed * (particle_2.mass - particle_1.mass) / total_mass)
                particle_2_vector_b = (angle + math.pi, 2 *
                                     particle_1.speed * particle_1.mass / total_mass)
                particle_2.angle, particle_2.speed = self.add_vectors(
                    particle_2_vector_a, particle_2_vector_b)

                elasticity: float = particle_1.elasticity * particle_2.elasticity
                particle_1.speed *= elasticity
                particle_2.speed *= elasticity

                # At the time, we detect the collision, the particles' circles could possibly have overlapped
                # We correct their positions to remove this overlap
                overlap: float = 0.5 * \
                    (particle_1.size_px + particle_2.size_px - distance + 1)
                particle_1.x_px += math.sin(angle) * overlap
                particle_1.y_px -= math.cos(angle) * overlap
                particle_2.x_px -= math.sin(angle) * overlap
                particle_2.y_px += math.cos(angle) * overlap

            return True

    def bounce(self, particle) -> bool:
        """
        Function to check if a particle (or any of its child instance classes)
        hits the environment boundary and if so, make it bounce.

        Returns: True if the particle hits a boundary.   
        """
        hit: bool = False
        # If particle crosses left border:
        if particle.x_px < particle.size_px:
            particle.x_px = 2 * particle.size_px - particle.x_px
            particle.angle = - particle.angle
            particle.speed *= self.elasticity
            hit = True

        # if particle crosses right border:
        elif particle.x_px > self.width_px - particle.size_px:
            particle.x_px = 2 * (self.width_px - particle.size_px) - particle.x_px
            particle.angle = - particle.angle
            particle.speed *= self.elasticity
            hit = True

        # if particle crosses top border:
        if particle.y_px < particle.size_px:
            particle.y_px = 2 * particle.size_px - particle.y_px
            particle.angle = math.pi - particle.angle
            particle.speed *= self.elasticity
            hit = True

        # if particle crosses bottom border:
        elif particle.y_px > self.height_px - particle.size_px:
            particle.y_px = 2 * (self.height_px - particle.size_px) - particle.y_px
            particle.angle = math.pi - particle.angle
            particle.speed *= self.elasticity
            hit = True

        return hit
