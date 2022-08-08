"""
Tutorial Grease Pencil
Sources:
    - [Blender 2.8 Grease Pencil Scripting and Generative Art](https://towardsdatascience.com/blender-2-8-grease-pencil-scripting-and-generative-art-cbbfd3967590)
"""
# =====================================================================
# Import modules
# =====================================================================

# import internal modules
# from typing import List, Set, Dict, TypedDict, Tuple, Optional, Union
import math
from math import sin, cos

# import 3rd-party modules
import bpy
import numpy as np
import numpy.typing as npt

# import local modules

# =====================================================================
# Define functions
# =====================================================================

def get_grease_pencil(gpencil_obj_name="GPencil") -> bpy.types.GreasePencil:
    """
    Return the grease-pencil object with the given name. Initialize one if not already present.
    :param gpencil_obj_name: name/key of the grease pencil object in the scene
    """

    # If not present already, create grease pencil object
    if gpencil_obj_name not in bpy.context.scene.objects:
        bpy.ops.object.gpencil_add(align="WORLD", location=(0, 0, 0), type='EMPTY')
        # rename grease pencil
        bpy.context.scene.objects[-1].name = gpencil_obj_name

    # Get grease pencil object
    gpencil = bpy.context.scene.objects[gpencil_obj_name]

    return gpencil

def get_grease_pencil_layer(gpencil: bpy.types.GreasePencil, gpencil_layer_name='GP_Layer',
                            clear_layer=False) -> bpy.types.GPencilLayer:
    """
    Return the grease-pencil layer with the given name. Create one if not already present.
    :param gpencil: grease-pencil object for the layer data
    :param gpencil_layer_name: name/key of the grease pencil layer
    :param clear_layer: whether to clear all previous layer data
    """

    # Get grease pencil layer or create one if none exists
    if gpencil.data.layers and gpencil_layer_name in gpencil.data.layers:
        gpencil_layer = gpencil.data.layers[gpencil_layer_name]
    else:
        gpencil_layer = gpencil.data.layers.new(gpencil_layer_name, set_active=True)

    if clear_layer:
        gpencil_layer.clear()  # clear all previous layer data

    # bpy.ops.gpencil.paintmode_toggle()  # need to trigger otherwise there is no frame

    return gpencil_layer

# Util for default behavior merging previous two methods
def init_grease_pencil(gpencil_obj_name='GPencil', gpencil_layer_name='GP_Layer',
                       clear_layer=True) -> bpy.types.GPencilLayer:
    gpencil = get_grease_pencil(gpencil_obj_name)
    gpencil_layer = get_grease_pencil_layer(gpencil, gpencil_layer_name, clear_layer=clear_layer)
    return gpencil_layer


def draw_lines(
    gp_frame, points: npt.NDArray[np.float],
    use_cyclic=False, line_thickness=1, material_index=0):
    
    # get nb of points
    nb_points = len(points)
    
    # Init new stroke
    gp_stroke = gp_frame.strokes.new()
    gp_stroke.display_mode = '3DSPACE'  # allows for editing

    # close stroke if asked
    if use_cyclic:
        gp_stroke.use_cyclic = True

    # set material thickness
    gp_stroke.line_width = line_thickness

    # set material index (0 by default); material must have been alreay created 
    gp_stroke.material_index = material_index

    # Define stroke geometry
    gp_stroke.points.add(count=nb_points)
    
    for i in range(nb_points):
        gp_stroke.points[i].co = points[i]

    # set origin to geometry of active object (i.e grease pencil)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
        
    return gp_stroke


def draw_square(gp_frame, center_location=(0,0,0), line_size=1, line_thickness=1, material_index=0):
    """
    Function to draw grease pencil square
    """
    line_half_size = line_size/2
    left_x = center_location[0] - line_half_size
    right_x = center_location[0] + line_half_size

    bottom_y = center_location[1] - line_half_size
    top_y = center_location[1] + line_half_size


    top_left = left_x, top_y, center_location[2]
    top_right = right_x, top_y, center_location[2]
    bottom_right = right_x, bottom_y, center_location[2]
    bottom_left = left_x, bottom_y, center_location[2]

    points = np.array([
        top_left, 
        top_right, 
        bottom_right,
        bottom_left
         ])

    gp_stroke = draw_lines(gp_frame, points, use_cyclic=True, line_thickness=line_thickness, material_index=material_index)

    return gp_stroke


def draw_circle(gp_frame, center_location=(0, 0, 0), radius=1, segments=32, line_thickness=1, material_index=0):

    # Init new stroke
    gp_stroke = gp_frame.strokes.new()
    gp_stroke.display_mode = '3DSPACE'  # allows for editing
    gp_stroke.use_cyclic = True        # closes the stroke
    
    # set material thickness
    gp_stroke.line_width = line_thickness

    # set material index (0 by default); material must have been alreay created 
    gp_stroke.material_index = material_index

    # Define stroke geometry
    angle = 2*math.pi/segments  # angle in radians
    gp_stroke.points.add(count=segments)
    for i in range(segments):
        x = center_location[0] + radius*math.cos(angle*i)
        y = center_location[1] + radius*math.sin(angle*i)
        z = center_location[2]
        gp_stroke.points[i].co = (x, y, z)

    return gp_stroke


def rotate_stroke(stroke, angle, axis='z'):

    axis = axis.lower()

    # Define rotation matrix based on axis
    if axis == 'x':
        transform_matrix = np.array([[1, 0, 0],
                                     [0, cos(angle), -sin(angle)],
                                     [0, sin(angle), cos(angle)]])
    elif axis == 'y':
        transform_matrix = np.array([[cos(angle), 0, -sin(angle)],
                                     [0, 1, 0],
                                     [sin(angle), 0, cos(angle)]])
    # default on z
    else:
        transform_matrix = np.array([[cos(angle), -sin(angle), 0],
                                     [sin(angle), cos(angle), 0],
                                     [0, 0, 1]])

    # Apply rotation matrix to each point
    for p in stroke.points:
        p.co = transform_matrix @ np.array(p.co).reshape(3, 1) # @ operator means matrix multiplication


def draw_sphere(gp_frame, nb_circles: int, center_location=(0, 0, 0), radius=1, segments=32, axis="x", line_thickness=1, material_index=0):
    angle = 2 * math.pi / nb_circles
    for i in range(nb_circles):
        circle = draw_circle(gp_frame, center_location=center_location, radius=radius, segments=segments, line_thickness=line_thickness, material_index=material_index)
        rotate_stroke(circle, angle*i, axis)


def draw_rotated_square(gp_frame, nb_squares: int, center_location=(0, 0, 0), line_size=1, axis="x", line_thickness=1, material_index=0):
    angle = 2 * math.pi / nb_squares
    for i in range(nb_squares):
        square = draw_square(gp_frame, center_location=center_location, line_size=line_size, line_thickness=line_thickness, material_index=material_index)
        rotate_stroke(square, angle*i, axis)