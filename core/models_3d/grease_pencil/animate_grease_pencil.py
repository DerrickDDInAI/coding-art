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
import sys
from pathlib import Path

# import 3rd-party modules
import bpy
import numpy as np
import numpy.typing as npt

# import local modules
# add current working directory to be able 
# cwd = Path(__file__).parent.resolve()
cwd = Path("/Users/derrickvanfrausum/BeCode_AI/git-repos/coding-art/core/models_3d/grease_pencil")
sys.path.append(str(cwd))

# utils = bpy.data.texts["utils.py"].as_module()

from utils import *

# =====================================================================
# Define constants & variables
# =====================================================================

LINE_THICKNESS = 200
SEGMENTS = 32
CENTER_LOCATION = (0, 0, 0)
NB_RINGS = 10
ANGLE = 10
MIN_RADIUS = 0.5
MIN_SQUARE_SIZE = 0.5

NUM_FRAMES = 120
FRAMES_SPACING = 1  # distance between frames

COPY_FRAME = False

# set start and end frames
bpy.context.scene.frame_start = 0
bpy.context.scene.frame_end = NUM_FRAMES*FRAMES_SPACING

# =====================================================================
# Draw & animate
# =====================================================================



# initialize grease pencil
gp_layer = init_grease_pencil()


# draw stroke at each frame 
for frame in range(NUM_FRAMES):

    if not COPY_FRAME:
        gp_frame = gp_layer.frames.new(frame*FRAMES_SPACING)

    else:
        # create new grease pencil layer at frame 0 
        if frame == 0:
            gp_frame = gp_layer.frames.new(frame*FRAMES_SPACING)
        
        # then copy content from current frame to next available frame
        else:
            gp_layer.frames.copy(gp_frame) # copy the content of the given frame to the next available timeline slot.

    draw_sphere(gp_frame, nb_circles=20, center_location=CENTER_LOCATION, radius=MIN_RADIUS+frame, segments=SEGMENTS, axis="x", line_thickness=LINE_THICKNESS, material_index=0)
    draw_sphere(gp_frame, nb_circles=20, center_location=CENTER_LOCATION, radius=MIN_RADIUS+frame, segments=SEGMENTS, axis="y", line_thickness=LINE_THICKNESS, material_index=0)
    draw_rotated_square(gp_frame, nb_squares=10, center_location=CENTER_LOCATION, line_size=MIN_SQUARE_SIZE+frame, axis="x", line_thickness=LINE_THICKNESS, material_index=0)
    draw_rotated_square(gp_frame, nb_squares=10, center_location=CENTER_LOCATION, line_size=MIN_SQUARE_SIZE+frame, axis="y", line_thickness=LINE_THICKNESS, material_index=0)

    # draw sphere + ring
    draw_sphere(gp_frame, nb_circles=20, center_location=CENTER_LOCATION, radius=MIN_RADIUS, segments=SEGMENTS, axis="y", line_thickness=LINE_THICKNESS, material_index=2)
    circle = draw_circle(gp_frame, center_location=(0,0,0), radius=MIN_RADIUS * 2, segments=SEGMENTS, line_thickness=LINE_THICKNESS, material_index=1)
    rotate_stroke(circle, ANGLE, axis="x")
    
    # draw saturn rings
    NB_RINGS = 10

    for i in range(NB_RINGS):
        circle = draw_circle(gp_frame, center_location=(0,0,0), radius=MIN_RADIUS -(i * frame/15) + frame * i/5, segments=SEGMENTS, line_thickness=LINE_THICKNESS, material_index=0)
        rotate_stroke(circle, ANGLE, axis="x")
