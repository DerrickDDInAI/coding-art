"""
Python script to plot and animate 3D bars of sport data
Sources:
    - [Blender.stackexchange - How to add text in blender using python](https://blender.stackexchange.com/questions/163487/how-to-add-text-in-blender-using-python)
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
import pandas as pd
import numpy as np
from mathutils import Vector, Matrix


# import local modules
current_working_directory = Path(__file__).parent.resolve()
# current_working_directory = "/Users/derrickvanfrausum/BeCode_AI/git-repos/coding-art/core/models_3d/blender_utils.py"
sys.path.append(current_working_directory)

import blender_utils

# =====================================================================
# Define functions
# =====================================================================

def create_animated_bar(
    ys, x, 
    collection_name,
    bar_center_location_x,
    nb_frames = 30, show_labels=True,
    ys_label_collection_name= "Ys_label_collection",
    x_label_collection_name="X_label_collection",
    parent_label_collection_name="Label_collection"
    ):
    """
    Function to animate a bar (for a barplot)
    """
    
    # get cube layer collection in outliner and activate it
    layer_collection = bpy.context.view_layer.layer_collection.children['Collection'].children[collection_name]
    bpy.context.view_layer.active_layer_collection = layer_collection

    # if enabled, show labels
    if show_labels:

        # get parent label collection if exists or else none
        parent_label_collection = bpy.data.collections.get(parent_label_collection_name)

        # create parent label collection in default collection if it doesn't exist
        if parent_label_collection is None:
            parent_label_collection = blender_utils.create_collection(parent_label_collection_name, bpy.data.collections['Collection'])

        # get x label collection if it exists or else none
        x_label_collection = bpy.data.collections.get(x_label_collection_name)

        # create x_label_collection in its parent collection if it doesn't exist
        if x_label_collection is None:
            x_label_collection = blender_utils.create_collection(x_label_collection_name, parent_label_collection)

        # add x label text
        date_text_obj = blender_utils.add_text(x, collection=x_label_collection)
        date_text_obj.rotation_euler[0] = 1.5708 # 90°
        date_text_obj.scale = (0.2, 0.2, 0.2)
        date_text_obj.location = (bar_center_location_x - CUBE_SIZE/2, -CUBE_SIZE/2, -0.4)


# =====================================================================
# Declare constants and variables
# =====================================================================

# set number of frames for the animation
FRAME_START = 0
FRAME_END = 30
nb_frames = FRAME_END - FRAME_START

# set size of cubes
CUBE_SIZE = 1 


# =====================================================================
# Set the scene
# =====================================================================

# reset scene by erasing everything
blender_utils.reset_scene()

# set scene frame start and end 
blender_utils.set_scene_frame_range(bpy.context.scene, frame_start=FRAME_START, frame_end=FRAME_END)

# get default collection
parent_collection = bpy.data.collections["Collection"]

## create collections
# set collection names
cube_collection_name = "Cube_collection"
text_collection_name = "Text_collection"
date_collection_name = "Dates_collection"
distance_collection_name = "Distance_collection"

# create collections in their respective parent collections
cube_collection = blender_utils.create_collection(cube_collection_name, parent_collection)
text_collection = blender_utils.create_collection(text_collection_name, parent_collection)
date_collection = blender_utils.create_collection(date_collection_name, text_collection)
distance_collection = blender_utils.create_collection(distance_collection_name, text_collection)


# =====================================================================
# Read data
# =====================================================================

# read csv file into pandas dataframe
df = pd.read_csv("/Users/derrickvanfrausum/BeCode_AI/git-repos/coding-art/core/assets/data/garmin_data/football_1_year_cleaned.csv")

# get list of dates (without duplicates) and sort it
dates = df["Date_yy-mm-dd"].unique()
dates.sort()


# =====================================================================
# Create animation
# =====================================================================

for i, activity_date in enumerate(dates):
    activities = df.loc[df["Date_yy-mm-dd"] == activity_date, ["Date_yy-mm-dd", "Distance"]]
    distance_done = 0
    animate_distance_done = 0
    
    text_obj = blender_utils.add_text(activity_date, collection=date_collection)
    text_obj.rotation_euler[0] = 1.5708 # 90°
    text_obj.scale = (0.2, 0.2, 0.2)
    text_obj.location = (i - CUBE_SIZE/2, -CUBE_SIZE/2, -0.4)
    

    for activity in activities.values:
        distance = activity[1]
        # offset_location = distance/2
        # distance_done += distance
        
        # toDo: fix when CUBE_SIZE != 1
        # bpy.ops.mesh.primitive_cube_add(size=CUBE_SIZE, enter_editmode=False, align='WORLD', location=(i, 0, distance_done - distance/2), scale=(1, 1, distance))
        bpy.ops.mesh.primitive_cube_add(size=CUBE_SIZE, enter_editmode=False, align='WORLD', location=(i, 0, 0), scale=(1, 1, 1))
        # bpy.ops.mesh.primitive_cube_add(size=CUBE_SIZE, enter_editmode=False, align='WORLD', location=(i, 0, 0), scale=(1, 1, distance))
        obj = bpy.context.active_object
        
        # move origin to bottom of object (z axis)
        # new_origin = Vector([0,0,- distance_done + distance/2])
        # obj = bpy.context.active_object
        # obj.data.transform(Matrix.Translation(-new_origin))
        ## obj.matrix_world.translation += new_origin
        
        distance_linspace = np.linspace(0,distance,30)
        for frame_nb, d in enumerate(distance_linspace):
            # distance_done += d # cool animation
            # obj.location[2] = distance_done + d/2 
            obj.location[2] = animate_distance_done + d/2
            obj.keyframe_insert(data_path = "location", frame = frame_nb)
            obj.scale = (1,1,d)
            obj.keyframe_insert(data_path = "scale", frame = frame_nb)
            
        animate_distance_done += distance
        
    text_obj = blender_utils.add_text(f"{distance_done:.2f}", collection=distance_collection)
    text_obj.rotation_euler[0] = 1.5708 # 90°
    text_obj.scale = (0.2, 0.2, 0.2)
    text_obj.location = (i - CUBE_SIZE/2, -CUBE_SIZE/2, distance_done+0.4)

