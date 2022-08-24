"""
# Python script to plot and animate 3D bars of sport data
## Sources:
    - [Blender.stackexchange - How to add text in blender using python](https://blender.stackexchange.com/questions/163487/how-to-add-text-in-blender-using-python)
    - [How to install Python modules in Blender using pip](http://www.codeplastic.com/2019/03/12/how-to-install-python-modules-in-blender/)

## toDo: 
- fix create x and y label collections
- add modifiers, materials
- add calories inside rectangle (with wireframe modifier) as density of rectangle
- add blinking equal to average HR: normalize heartrate (as we have negative values for now)

## tips:
- to install dependency in blender python:
    * open blender
    * go to console
    * run: "import sys; sys.path" to see where blender python is
    * go to folder and open terminal at folder
    * run: "./bin/python3.10 -m pip install <some_package>" to install dependencies
    (e.g.: "./bin/python3.10 -m pip install scipy")

"""
# =====================================================================
# Import modules
# =====================================================================

# import internal modules
# from typing import List, Set, Dict, TypedDict, Tuple, Optional, Union
from calendar import c
import sys
from pathlib import Path
from uuid import uuid4
import colorsys

# import 3rd-party modules
import bpy
import pandas as pd
import numpy as np
# from mathutils import Vector, Matrix
from bpy.app.handlers import persistent


# import local modules
# current_working_directory = Path(__file__).parent.resolve()
utility_directory = "/Users/derrickvanfrausum/BeCode_AI/git-repos/coding-art/core/models_3d"
current_working_directory = "/Users/derrickvanfrausum/BeCode_AI/git-repos/coding-art/core/models_3d/data_visualization/sports"
sys.path.append(utility_directory)
sys.path.append(current_working_directory)

import blender_utils
import simulate_heartrate

# =====================================================================
# Define functions
# =====================================================================

def normalize_between_range(xs, a, b):
    """
    Function to normalize a series between range [a,b]
    """
    min_x = np.min(xs)
    max_x = np.max(xs)
    return (b - a) * (xs - min_x)/(max_x - min_x) + a

def create_animated_bar(
    ys, x,
    bar_collection_name,
    bar_center_location_x,
    bar_default_size,
    # nb_frames=30, 
    frame_start = 0,
    frame_end = 30,
    show_labels=True,
    y_label_collection_name= "Y_label_collection",
    x_label_collection_name="X_label_collection",
    parent_label_collection_name="Label_collection",
    y_label_prefix="",
    z_dict=None,
    wireframe=False
    ):
    """
    Function to animate a bar (for a barplot)

    ys with "s" because there could be multiple y values for one x
    * x label texts are fixed.
    * y label texts change as the bar grows in the z axis at each frame
    """

    # set initial values
    nb_frames = frame_end - frame_start
    total_y = 0.00
    previous_y_linspace = np.zeros(nb_frames)
    label_location_offset = 0.4

    ## 1. Add labels if enabled

    # if enabled, show labels
    if show_labels:

        # set variables
        label_scale = 0.2 * bar_default_size
        bar_middle_size = bar_default_size/2

        # get parent label collection if exists or else none
        parent_label_collection = bpy.data.collections.get(parent_label_collection_name)

        # create parent label collection in default collection if it doesn't exist
        if parent_label_collection is None:
            parent_label_collection = blender_utils.create_collection(parent_label_collection_name, bpy.data.collections['Collection'])

        # get x and y label collections if they exist or else none
        x_label_collection = bpy.data.collections.get(x_label_collection_name)
        y_label_collection = bpy.data.collections.get(y_label_collection_name)

        # create x and y label collections in their parent collection if they don't exist
        if x_label_collection is None:
            x_label_collection = blender_utils.create_collection(x_label_collection_name, parent_label_collection)
        
        if y_label_collection is None:
            y_label_collection = blender_utils.create_collection(y_label_collection_name, parent_label_collection)

        # add x label text and set transform properties
        x_text_obj = blender_utils.add_text(x, collection=parent_label_collection)
        x_text_obj.rotation_euler[0] = 1.5708 # 90°
        x_text_obj.scale = (label_scale, label_scale, label_scale)
        x_text_obj.location = (bar_center_location_x - bar_middle_size, -bar_middle_size, -label_location_offset)

        # # activate x label text object
        # bpy.context.view_layer.objects.active = x_text_obj

        # # add modifier to x label
        # bpy.ops.object.modifier_add(type='SOLIDIFY')
        # bpy.context.object.modifiers["Solidify"].thickness = 0.27
        modifier = x_text_obj.modifiers.new(name="solidify", type="SOLIDIFY")
        modifier.thickness = 0.27

        # add material shader with specified settings
        r,g,b = np.array((222,183,40))/255
        a = 1
        settings_dict = {
            'Color': (r, g, b, a),
            'Strength': 3
        }
        material, shader = blender_utils.add_shader(material_name=f"x_text_material_{uuid4()}", type="ShaderNodeEmission", settings_dict=settings_dict)

        # apply the material to cube object
        x_text_obj.data.materials.append(material)
        
        # add y label text and set transform properties (add initial y text that will be updated at each frame)
        y_text_obj = blender_utils.add_text(f"{total_y:.2f} km", collection=parent_label_collection)
        y_text_obj.rotation_euler[0] = 1.5708 # 90°
        y_text_obj.scale = (label_scale, label_scale, label_scale)
        y_text_obj.location = (bar_center_location_x - bar_middle_size, -bar_middle_size, total_y+label_location_offset)

        # activate y label text object
        # bpy.context.view_layer.objects.active = y_text_obj

        # add modifier to y label
        # bpy.ops.object.modifier_add(type='SOLIDIFY')
        # bpy.context.object.modifiers["Solidify"].thickness = 0.27
        modifier = y_text_obj.modifiers.new(name="solidify", type="SOLIDIFY")
        modifier.thickness = 0.27
        
        # add material shader with specified settings
        r,g,b = np.array((221,17,17))/255
        a = 1
        settings_dict = {
            'Color': (r, g, b, a),
            'Strength': 3
        }
        material, shader = blender_utils.add_shader(material_name=f"y_text_material_{uuid4()}", type="ShaderNodeEmission", settings_dict=settings_dict)

        # apply the material to cube object
        y_text_obj.data.materials.append(material)

    
    ## 2. Create bar

    # get parent label collection if exists or else none
    bar_collection = bpy.data.collections.get(bar_collection_name)

    # create parent label collection in default collection if it doesn't exist
    if bar_collection is None:
        bar_collection = blender_utils.create_collection(bar_collection_name, bpy.data.collections['Collection'])


    # get cube layer collection in outliner and activate it
    layer_collection = bpy.context.view_layer.layer_collection.children['Collection'].children[bar_collection_name]
    bpy.context.view_layer.active_layer_collection = layer_collection

    # iterate over y values
    for z_idx, y in enumerate(ys):

        # add cube
        bpy.ops.mesh.primitive_cube_add(size=bar_default_size, enter_editmode=False, align='WORLD', location=(bar_center_location_x, 0, 0), scale=(bar_default_size, bar_default_size, bar_default_size))

        # get cube object (current active object as it has just been created)
        cube_obj = bpy.context.active_object

        # if z_dict with values for modifier and material properties
        if z_dict is not None:

            # add uv sphere to use for particle system
            bpy.ops.mesh.primitive_uv_sphere_add(enter_editmode=False, align='WORLD', location=(-10 - z_idx, -10, -10), scale=(1, 1, 1))

            # get sphere object (current active object as it has just been created)
            sphere_obj = bpy.context.active_object

            # add particle system
            ps = cube_obj.modifiers.new("particle_system", 'PARTICLE_SYSTEM')

            # get particle system
            psys = cube_obj.particle_systems[ps.name]

            # set settings
            psys.settings.type = 'EMITTER'
            psys.settings.count = int(z_dict["modifier"].iloc[z_idx])
            psys.settings.frame_start = frame_start
            psys.settings.frame_end = frame_end
            psys.settings.lifetime = nb_frames
            psys.settings.emit_from = 'VOLUME'
            psys.settings.distribution = 'RAND' # random distribution
            psys.settings.physics_type = 'NO'
            psys.settings.render_type = 'OBJECT'
            psys.settings.instance_object = sphere_obj
            psys.settings.particle_size = 0.033

            #input
            (h, s, v) = (z_dict["material"].iloc[z_idx], 244, 85)
            #normalize
            (h, s, v) = (h / 179, s / 255, v / 255)
            #convert to RGB
            (r, g, b) = colorsys.hsv_to_rgb(h, s, v)

            # add material shader with specified settings
            # r = (z_dict["material"].iloc[z_idx]/200)*255
            # r,g,b = np.array((r,215,4))/255
            a = 1
            settings_dict = {
                'Color': (r, g, b, a),
                # 'Strength': (z_dict["material"].iloc[z_idx]/100)**3
            }
            ps_material, ps_shader = blender_utils.add_shader(material_name=f"sphere_material_{uuid4()}", type="ShaderNodeEmission", settings_dict=settings_dict)

            # apply the material to cube object
            sphere_obj.data.materials.append(ps_material)

            # get simulated heartrate values
            simulated_heartrates = simulate_heartrate.simulate_heartbeat([z_dict["material"].iloc[z_idx]], capture_length=int(np.max([1, nb_frames * 30])))
        
        
        # add wireframe modifier
        if wireframe:
            modifier = cube_obj.modifiers.new(name="wireframe", type="WIREFRAME")

        # add material shader with specified settings
        r,g,b = np.array((7,26,222))/255
        a = 1
        settings_dict = {
            'Color': (r, g, b, a),
            'Strength': 20
        }
        material, shader = blender_utils.add_shader(material_name=f"cube_obj_material_{uuid4()}", type="ShaderNodeEmission", settings_dict=settings_dict)

        # apply the material to cube object
        cube_obj.data.materials.append(material)


        # get n (nb of frames) evenly spaced y samples
        y_linspace = np.linspace(0, y, nb_frames)
 
        # iterate over y samples
        for frame_nb, sample_y in enumerate(y_linspace):

            # set cube transform properties and add corresponding keyframes
            cube_obj.location[2] = previous_y_linspace[frame_nb] + sample_y/2
            cube_obj.keyframe_insert(data_path="location", frame=frame_nb)
            cube_obj.scale = (1, 1, sample_y)
            cube_obj.keyframe_insert(data_path="scale", frame=frame_nb)

            # set material value with values from simulated hearbeat and add keyframe
            ps_material.node_tree.nodes[ps_shader.name].inputs["Strength"].default_value = simulated_heartrates[frame_nb]
            ps_material.node_tree.nodes[ps_shader.name].inputs["Strength"].keyframe_insert("default_value", frame=frame_nb)
        
        # add y samples to previous y samples to get the total y values per frame
        previous_y_linspace += y_linspace

    
    ## 3. Update y labels if show labels enabled

    # if show labels enabled
    if show_labels:

        # iterate over frame numbers
        for frame_nb in range(nb_frames):

            # set y label text transform properties and add corresponding keyframes
            y_text_obj.location[2] = previous_y_linspace[frame_nb] + label_location_offset
            y_text_obj.keyframe_insert(data_path="location", frame=frame_nb)


        previous_y_linspace = [f"{y:.2f} {y_label_prefix}" for y in previous_y_linspace]

        # update text
        @persistent
        def update(scene):
            # blender_utils.update_text_handler(scene, y_text_obj, np.around(previous_y_linspace, decimals=2))
            blender_utils.update_text_handler(scene, y_text_obj, previous_y_linspace)
        
        bpy.app.handlers.frame_change_pre.append(update)

    
    # set current frame to 0
    bpy.context.scene.frame_set(0)


# =====================================================================
# Declare constants and variables
# =====================================================================

# set number of frames for the animation
FRAME_START = 0
FRAME_END = 30*10
nb_frames = FRAME_END - FRAME_START

# set size of cubes
CUBE_SIZE = 1 


# =====================================================================
# Set the scene and render settings
# =====================================================================

# reset scene by erasing everything
blender_utils.reset_scene()

# set scene frame start and end 
blender_utils.set_scene_frame_range(bpy.context.scene, frame_start=FRAME_START, frame_end=FRAME_END)

# set dark world
blender_utils.set_default_world(color_rgba=(0,0,0,1))

# set render settings
blender_utils.set_default_eevee_render_settings()

# =====================================================================
# Read data
# =====================================================================

# read csv file into pandas dataframe
df = pd.read_csv("/Users/derrickvanfrausum/BeCode_AI/git-repos/coding-art/core/assets/data/garmin_data/football_1_year_cleaned.csv")

# get list of dates (without duplicates) and sort it
dates = df["Date_yy-mm-dd"].unique()[:3]
dates.sort()

# normalize calories_series to range of hue values [0,179] (toDo: add normalization to preprocessing data)
df.Calories = normalize_between_range(df.Calories, 0, 179)


# =====================================================================
# Create animation
# =====================================================================

# iterate over activity date
for bar_center_location_x, activity_date in enumerate(dates):

    # get activities for current date
    activities = df.loc[df["Date_yy-mm-dd"] == activity_date, "Distance"]
    
    # get average heart rates and calories for current date (to use their values as modifier or material properties)
    average_hr_series = df.loc[df["Date_yy-mm-dd"] == activity_date, "Avg HR"]
    calories_series = df.loc[df["Date_yy-mm-dd"] == activity_date, "Calories"]

    z_dict = {
        "material": average_hr_series,
        "modifier": calories_series
    }

    # create animated bar
    create_animated_bar(
        activities.values, activity_date, 
        bar_collection_name="Cube_collection",
        bar_center_location_x=bar_center_location_x,
        bar_default_size=CUBE_SIZE,
        # nb_frames=30, 
        frame_start=FRAME_START,
        frame_end=FRAME_END,
        show_labels=True,
        y_label_collection_name="Y_label_collection",
        x_label_collection_name="X_label_collection",
        parent_label_collection_name="Label_collection",
        y_label_prefix="km",
        z_dict=z_dict,
        wireframe=True
        )