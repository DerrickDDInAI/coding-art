"""
Tutorial Grease Pencil
Sources:
    - https://towardsdatascience.com/blender-2-8-grease-pencil-scripting-and-generative-art-cbbfd3967590
"""

# =====================================================================
# Import modules
# =====================================================================

# import internal modules
# from typing import List, Set, Dict, TypedDict, Tuple, Optional, Union
import math
from math import sin, cos
import sys
from pathlib import Path

# import 3rd-party modules
import bpy
import numpy as np
import numpy.typing as npt

# import local modules
current_working_directory = Path(__file__).parent.resolve()
sys.path.append(current_working_directory)

from utils import *

# =====================================================================
# Define constants & variables
# =====================================================================

LINE_THICKNESS = 50
SEGMENTS = 32
CENTER_LOCATION = (0, 0, 0)


# =====================================================================
# Draw
# =====================================================================

# initialize grease pencil
gp_layer = init_grease_pencil()
gp_frame = gp_layer.frames.new(0)



# points = np.array([[0,0,0], [1,1,0], [1,0,0]])
# draw_lines(gp_frame, points, use_cyclic=False, line_thickness=LINE_THICKNESS)
# draw_square(gp_frame, center_location=(0,0,0), line_size=6, line_thickness=LINE_THICKNESS, material_index=0)
# circle = draw_circle(gp_frame, center_location=CENTER_LOCATION, radius=3, segments=SEGMENTS, line_thickness=LINE_THICKNESS, material_index=0)
draw_sphere(gp_frame, nb_circles=10, center_location=CENTER_LOCATION, radius=2, segments=SEGMENTS, axis="x", line_thickness=LINE_THICKNESS, material_index=0)
draw_rotated_square(gp_frame, nb_squares=10, center_location=CENTER_LOCATION, line_size=2, axis="y", line_thickness=LINE_THICKNESS, material_index=0)


# # draw part of spheres centered
# NB_CIRCLES = 10
# nb_circles_1_mirror = NB_CIRCLES//2 + 1 # + 1 in the center

# angle = math.pi / (nb_circles_1_mirror*10)
# for i in range(nb_circles_1_mirror):
#     circle = draw_circle(gp_frame, center_location=CENTER_LOCATION, radius=3, segments=SEGMENTS, line_thickness=LINE_THICKNESS, material_index=0)
#     rotate_stroke(circle, angle*i, axis="x")
    
#     if i != 0:
#         circle = draw_circle(gp_frame, center_location=CENTER_LOCATION, radius=3, segments=SEGMENTS, line_thickness=LINE_THICKNESS, material_index=0)
#         rotate_stroke(circle, -angle*i, axis="x")

# draw saturn rings
NB_CIRCLES = 10

angle = 10
for i in range(NB_CIRCLES):
    circle = draw_circle(gp_frame, center_location=(0,0,0), radius=3-i/15, segments=SEGMENTS, line_thickness=LINE_THICKNESS, material_index=0)
    rotate_stroke(circle, angle, axis="x")