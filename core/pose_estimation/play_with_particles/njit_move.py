import math
from numba import njit

@njit
def njit_move_particles(particles_attributes, line_particles_attributes, environment_attributes, apply_collision=True):
    """
    Function to update the position of particles due to their speeds and angles.
    """
    height_px, width_px, air_mass, elasticity = environment_attributes

    new_particles_attributes = []

    # move particles
    for particle_1_name, particle_1_y_px, particle_1_x_px, particle_1_angle, particle_1_speed, particle_1_mass, particle_1_size_px, particle_1_elasticity in particles_attributes:

        # particle.move()
        particle_1_x_px += math.sin(particle_1_angle) * particle_1_speed
        particle_1_y_px -= math.cos(particle_1_angle) * particle_1_speed

        # world.add_air_resistance(particle)
        particle_1_speed *= (particle_1_mass/(particle_1_mass + air_mass)) ** particle_1_size_px

        # world.attraction(player_1, particle)
        # world.collide(particle, player_1, True)
        
        # world.bounce(particle)
        hit: bool = False
        # If particle crosses left border:
        if particle_1_x_px < particle_1_size_px:
            particle_1_x_px = 2 * particle_1_size_px - particle_1_x_px
            particle_1_angle = - particle_1_angle
            particle_1_speed *= elasticity
            hit = True

        # if particle crosses right border:
        elif particle_1_x_px > width_px - particle_1_size_px:
            particle_1_x_px = 2 * (width_px - particle_1_size_px) - particle_1_x_px
            particle_1_angle = - particle_1_angle
            particle_1_speed *= elasticity
            hit = True

        # if particle crosses top border:
        if particle_1_y_px < particle_1_size_px:
            particle_1_y_px = 2 * particle_1_size_px - particle_1_y_px
            particle_1_angle = math.pi - particle_1_angle
            particle_1_speed *= elasticity
            hit = True

        # if particle crosses bottom border:
        elif particle_1_y_px > height_px - particle_1_size_px:
            particle_1_y_px = 2 * (height_px - particle_1_size_px) - particle_1_y_px
            particle_1_angle = math.pi - particle_1_angle
            particle_1_speed *= elasticity
            hit = True
            
        # collision
        for particle_2_name, particle_2_y_px, particle_2_x_px, particle_2_angle, particle_2_speed, particle_2_mass, particle_2_size_px, particle_2_elasticity in particles_attributes:
            if particle_1_name != particle_2_name:
                # world.collide(particle, particle_2, True)
                # Get the distances in the x direction and in the y direction
                distance_x: float = particle_1_x_px - particle_2_x_px
                distance_y: float = particle_1_y_px - particle_2_y_px

                # Compute the distance between the 2 particles
                distance: float = math.hypot(distance_x, distance_y)

                # If distance < sum of particles' radius, it means collision
                if distance < particle_1_size_px + particle_2_size_px:
                    if apply_collision:
                        collision_angle: float = math.atan2(
                            distance_y, distance_x) + 0.5 * math.pi
                        total_mass: int = particle_1_mass + particle_2_mass

                        particle_1_vector_a = (particle_1_angle, particle_1_speed * (particle_1_mass - particle_2_mass) / total_mass)
                        particle_1_vector_b = (collision_angle, 2 * particle_2_speed * particle_2_mass / total_mass)
                            
                        # angle, speed = self.add_vectors(particle_1_vector_a, particle_1_vector_b)
                        angle_1: float
                        angle_2: float
                        magnitude_1: float
                        magnitude_2: float

                        angle_1, magnitude_1 = particle_1_vector_a
                        angle_2, magnitude_2 = particle_1_vector_b
                        x = math.sin(angle_1) * magnitude_1 + math.sin(angle_2) * magnitude_2
                        y = math.cos(angle_1) * magnitude_1 + math.cos(angle_2) * magnitude_2

                        particle_1_angle: float = 0.5 * math.pi - math.atan2(y, x)
                        particle_1_speed: float = math.hypot(x, y)

                        particle_2_vector_a = (
                            particle_2_angle, particle_2_speed * (particle_2_mass - particle_1_mass) / total_mass)
                        particle_2_vector_b = (collision_angle + math.pi, 2 *
                                            particle_1_speed * particle_1_mass / total_mass)

                        # particle_2_angle, particle_2_speed = self.add_vectors(particle_2_vector_a, particle_2_vector_b)
                        angle_1: float
                        angle_2: float
                        magnitude_1: float
                        magnitude_2: float

                        angle_1, magnitude_1 = particle_2_vector_a
                        angle_2, magnitude_2 = particle_2_vector_b
                        x = math.sin(angle_1) * magnitude_1 + math.sin(angle_2) * magnitude_2
                        y = math.cos(angle_1) * magnitude_1 + math.cos(angle_2) * magnitude_2

                        particle_2_angle: float = 0.5 * math.pi - math.atan2(y, x)
                        particle_2_speed: float = math.hypot(x, y)

                        collision_elasticity: float = particle_1_elasticity * particle_2_elasticity
                        particle_1_speed *= collision_elasticity
                        particle_2_speed *= collision_elasticity

                        # At the time, we detect the collision, the particles' circles could possibly have overlapped
                        # We correct their positions to remove this overlap
                        overlap: float = 0.5 * \
                            (particle_1_size_px + particle_2_size_px - distance + 1)
                        particle_1_x_px += math.sin(collision_angle) * overlap
                        particle_1_y_px -= math.cos(collision_angle) * overlap
                        particle_2_x_px -= math.sin(collision_angle) * overlap
                        particle_2_y_px += math.cos(collision_angle) * overlap


        for line_particle_name, line_particle_y_px, line_particle_x_px, line_particle_angle, line_particle_speed, line_particle_mass, line_particle_size_px, line_particle_elasticity  in line_particles_attributes:
            # world.attraction(particle, line_particle)
            # Get the distances in the x direction and in the y direction
            distance_x: float = particle_1_x_px - line_particle_x_px
            distance_y: float = particle_1_y_px - line_particle_y_px

            # Compute the distance between the 2 particles
            distance: float = math.hypot(distance_x, distance_y)

            # If distance < sum of particles' radius, it means collision;
            # No attraction effect anymore
            # if distance < size_px + line_particle_size_px:
            #     return True

            if distance >= particle_1_size_px + line_particle_size_px:
                # Use Newton's law of universal gravitation
                theta: float = math.atan2(distance_y, distance_x)
                force: float = 0.1 * particle_1_mass * line_particle_mass / distance**2
                vector = (theta - 0.5 * math.pi, force/particle_1_mass)
                # self.accelerate(particle_1, (theta - 0.5 * math.pi, force/mass))
                # particle.angle, particle.speed = self.add_vectors((particle.angle, particle.speed), vector)
                # angle, speed = self.add_vectors(particle_1_vector_a, particle_1_vector_b)
                angle_1: float
                angle_2: float
                magnitude_1: float
                magnitude_2: float
                
                angle_1, magnitude_1 = particle_1_angle, particle_1_speed
                angle_2, magnitude_2 = vector
                x = math.sin(angle_1) * magnitude_1 + math.sin(angle_2) * magnitude_2
                y = math.cos(angle_1) * magnitude_1 + math.cos(angle_2) * magnitude_2

                particle_1_angle: float = 0.5 * math.pi - math.atan2(y, x)
                particle_1_speed: float = math.hypot(x, y)


                vector = (theta - 0.5 * math.pi, force/line_particle_mass)
                # self.accelerate(particle_2, (theta + 0.5 * math.pi, force/particle_2.mass))
                # particle.angle, particle.speed = self.add_vectors((particle.angle, particle.speed), vector)
                
                angle_1: float
                angle_2: float
                magnitude_1: float
                magnitude_2: float

                angle_1, magnitude_1 = line_particle_angle, line_particle_speed
                angle_2, magnitude_2 = vector
                x = math.sin(angle_1) * magnitude_1 + math.sin(angle_2) * magnitude_2
                y = math.cos(angle_1) * magnitude_1 + math.cos(angle_2) * magnitude_2

                line_particle_angle: float = 0.5 * math.pi - math.atan2(y, x)
                line_particle_speed: float = math.hypot(x, y)

            # world.collide(particle, line_particle, True)
            # Get the distances in the x direction and in the y direction
            distance_x: float = particle_1_x_px - line_particle_x_px
            distance_y: float = particle_1_y_px - line_particle_y_px

            # Compute the distance between the 2 particles
            distance: float = math.hypot(distance_x, distance_y)

            # If distance < sum of particles' radius, it means collision
            if distance < particle_1_size_px + line_particle_size_px:
                if apply_collision:
                    collision_angle: float = math.atan2(
                        distance_y, distance_x) + 0.5 * math.pi
                    total_mass: int = particle_1_mass + line_particle_mass

                    particle_1_vector_a = (particle_1_angle, particle_1_speed * (particle_1_mass - line_particle_mass) / total_mass)
                    particle_1_vector_b = (collision_angle, 2 * line_particle_speed * line_particle_mass / total_mass)
                        
                    # angle, speed = self.add_vectors(particle_1_vector_a, particle_1_vector_b)
                    angle_1: float
                    angle_2: float
                    magnitude_1: float
                    magnitude_2: float

                    angle_1, magnitude_1 = particle_1_vector_a
                    angle_2, magnitude_2 = particle_1_vector_b
                    x = math.sin(angle_1) * magnitude_1 + math.sin(angle_2) * magnitude_2
                    y = math.cos(angle_1) * magnitude_1 + math.cos(angle_2) * magnitude_2

                    particle_1_angle: float = 0.5 * math.pi - math.atan2(y, x)
                    particle_1_speed: float = math.hypot(x, y)

                    line_particle_vector_a = (
                        line_particle_angle, line_particle_speed * (line_particle_mass - particle_1_mass) / total_mass)
                    line_particle_vector_b = (collision_angle + math.pi, 2 *
                                        particle_1_speed * particle_1_mass / total_mass)

                    # line_particle_angle, line_particle_speed = self.add_vectors(line_particle_vector_a, line_particle_vector_b)
                    angle_1: float
                    angle_2: float
                    magnitude_1: float
                    magnitude_2: float

                    angle_1, magnitude_1 = line_particle_vector_a
                    angle_2, magnitude_2 = line_particle_vector_b
                    x = math.sin(angle_1) * magnitude_1 + math.sin(angle_2) * magnitude_2
                    y = math.cos(angle_1) * magnitude_1 + math.cos(angle_2) * magnitude_2

                    line_particle_angle: float = 0.5 * math.pi - math.atan2(y, x)
                    line_particle_speed: float = math.hypot(x, y)

                    collision_elasticity: float = particle_1_elasticity * line_particle_elasticity
                    particle_1_speed *= collision_elasticity
                    line_particle_speed *= collision_elasticity

                    # At the time, we detect the collision, the particles' circles could possibly have overlapped
                    # We correct their positions to remove this overlap
                    overlap: float = 0.5 * \
                        (particle_1_size_px + line_particle_size_px - distance + 1)
                    particle_1_x_px += math.sin(collision_angle) * overlap
                    particle_1_y_px -= math.cos(collision_angle) * overlap
                    line_particle_x_px -= math.sin(collision_angle) * overlap
                    line_particle_y_px += math.cos(collision_angle) * overlap

        # # apply world gravity to particle
        # particle.angle, particle.speed = world.add_vectors((particle.angle, particle.speed), world.gravity)

        # limit particle speed
        if particle_1_speed > 20:
            particle_1_speed = 20

        new_particles_attributes.append((float(particle_1_name), float(particle_1_y_px), float(particle_1_x_px), float(particle_1_angle), float(particle_1_speed), float(particle_1_mass), float(particle_1_size_px), float(particle_1_elasticity)))

    return new_particles_attributes