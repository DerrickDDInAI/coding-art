"""
# Python script to plot and animate a grid of 3D bars of sport data
## Sources:
    - [Blender.stackexchange - How to add text in blender using python](https://blender.stackexchange.com/questions/163487/how-to-add-text-in-blender-using-python)
    - [How to install Python modules in  using pip](http://www.codeplastic.com/2019/03/12/how-to-install-python-modules-in-blender/)

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

- to install opencv:
    * main opencv: pip install opencv-python
    * contrib package for the extra features: pip install opencv-contrib-python

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
utility_directories = [
    "/Users/derrickvanfrausum/BeCode_AI/git-repos/coding-art/core/models_3d",
    "/Users/derrickvanfrausum/BeCode_AI/git-repos/coding-art/core/models_3d/data_visualization/sports"
]
sys.path.extend(utility_directories)

# current_working_directory = Path(__file__).parent.resolve()
# current_working_directory = "/Users/derrickvanfrausum/BeCode_AI/git-repos/coding-art/core/models_3d/data_visualization/sports"
# sys.path.append(current_working_directory)

import blender_utils
import data_utils


# =====================================================================
# Define functions
# =====================================================================

def get_heartrate_sin_wave(heartrate_per_min, fps, nb_frames):
    """
    Function to get a sinusoid from heartrate
    """
    heartrate_per_sec = heartrate_per_min/60
    nb_seconds = nb_frames/fps

    # get number of times the sinusoid reaches top (max value)
    nb_heartrate_max_values = heartrate_per_sec * nb_seconds * 2 * np.pi

    # get x and y sinusoid values
    try:
        x = np.arange(0,nb_heartrate_max_values,nb_heartrate_max_values/nb_frames)   # start, stop, step
        y = (np.sin(x) + 1)/2 # translate and normalize y values to have a sinusoid ranging from 0 to 1
    except:
        y = np.ones(nb_frames) * heartrate_per_sec
    return y

def create_animated_bar(
    zs, x, xys,
    bar_collection_name,
    bar_default_size,
    # nb_frames=30, 
    frame_start = 0,
    frame_end = 30,
    fps=30,
    show_labels=True,
    z_label_collection_name= "Z_label_collection",
    x_label_collection_name="X_label_collection",
    parent_label_collection_name="Label_collection",
    z_label_prefix="",
    z_dict=None,
    wireframe=False
    ):
    """
    Function to animate a bar (for a barplot)

    zs with "s" because there could be multiple z values for one x
    * x label texts are fixed.
    * z label texts change as the bar grows in the z axis at each frame
    """

    # set initial values
    nb_frames = frame_end - frame_start
    total_z = 0.00
    previous_z_linspace = np.zeros(nb_frames)
    label_location_offset = 0.4
    if len(z_label_prefix) > 0: z_label_prefix = f" {z_label_prefix}"

    bar_center_location_x, bar_center_location_y = xys.iloc[0][1:-1].split(",")
    bar_center_location_x, bar_center_location_y = float(bar_center_location_x),float(bar_center_location_y)

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

        # get x and z label collections if they exist or else none
        x_label_collection = bpy.data.collections.get(x_label_collection_name)
        z_label_collection = bpy.data.collections.get(z_label_collection_name)

        # create x and z label collections in their parent collection if they don't exist
        if x_label_collection is None:
            x_label_collection = blender_utils.create_collection(x_label_collection_name, parent_label_collection)
        
        if z_label_collection is None:
            z_label_collection = blender_utils.create_collection(z_label_collection_name, parent_label_collection)

        # add x label text and set transform properties
        x_text_obj = blender_utils.add_text(x, collection=parent_label_collection)
        x_text_obj.rotation_euler[0] = 1.5708 # = 90°
        x_text_obj.scale = (label_scale, label_scale, label_scale)
        x_text_obj.location = (bar_center_location_x - bar_middle_size, bar_center_location_y - bar_middle_size, -label_location_offset)

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
        
        # add y label text and set transform properties (add initial z text that will be updated at each frame)
        z_text_obj = blender_utils.add_text(f"{total_z:.2f}{z_label_prefix}", collection=parent_label_collection)
        z_text_obj.rotation_euler[0] = 1.5708 # 90°
        z_text_obj.scale = (label_scale, label_scale, label_scale)
        z_text_obj.location = (bar_center_location_x - bar_middle_size, bar_center_location_y - bar_middle_size, total_z+label_location_offset)

        # activate y label text object
        # bpy.context.view_layer.objects.active = z_text_obj

        # add modifier to z label
        # bpy.ops.object.modifier_add(type='SOLIDIFY')
        # bpy.context.object.modifiers["Solidify"].thickness = 0.27
        modifier = z_text_obj.modifiers.new(name="solidify", type="SOLIDIFY")
        modifier.thickness = 0.27
        
        # add material shader with specified settings
        r,g,b = np.array((221,17,17))/255
        a = 1
        settings_dict = {
            'Color': (r, g, b, a),
            'Strength': 3
        }
        material, shader = blender_utils.add_shader(material_name=f"z_text_material_{uuid4()}", type="ShaderNodeEmission", settings_dict=settings_dict)

        # apply the material to cube object
        z_text_obj.data.materials.append(material)

    
    ## 2. Create bar

    # get parent label collection if exists or else none
    bar_collection = bpy.data.collections.get(bar_collection_name)

    # create parent label collection in default collection if it doesn't exist
    if bar_collection is None:
        bar_collection = blender_utils.create_collection(bar_collection_name, bpy.data.collections['Collection'])


    # get cube layer collection in outliner and activate it
    layer_collection = bpy.context.view_layer.layer_collection.children['Collection'].children[bar_collection_name]
    bpy.context.view_layer.active_layer_collection = layer_collection

    # iterate over z values
    for z_idx, z in enumerate(zs):

        if pd.isna(z): z = 0.0001

        # add cube
        bpy.ops.mesh.primitive_cube_add(size=bar_default_size, enter_editmode=False, align='WORLD', location=(bar_center_location_x, bar_center_location_y, 0), scale=(bar_default_size, bar_default_size, bar_default_size))

        # get cube object (current active object as it has just been created)
        cube_obj = bpy.context.active_object

        # if z_dict with values for modifier and material properties
        if z_dict is not None:

            modifier_value = z_dict["modifier"].iloc[z_idx]
            if pd.isna(modifier_value): modifier_value = 0.0001

            material_value = z_dict["material"].iloc[z_idx]
            if pd.isna(material_value): material_value = 0.0001

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
            psys.settings.count = int(modifier_value)
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
            (h, s, v) = (material_value, 244, 85)
            #normalize
            (h, s, v) = (h / 179, s / 255, v / 255)
            #convert to RGB
            (r, g, b) = colorsys.hsv_to_rgb(h, s, v)

            # add material shader with specified settings
            # r = (material_value/200)*255
            # r,g,b = np.array((r,215,4))/255
            a = 1
            settings_dict = {
                'Color': (r, g, b, a),
                # 'Strength': (material_value/100)**3
            }
            ps_material, ps_shader = blender_utils.add_shader(material_name=f"sphere_material_{uuid4()}", type="ShaderNodeEmission", settings_dict=settings_dict)

            # apply the material to cube object
            sphere_obj.data.materials.append(ps_material)

            # get simulated heartrate values
            # simulated_heartrates = simulate_heartrate.simulate_heartbeat([material_value], capture_length=int(np.max([1, nb_frames * 30])))

            # heartrate_per_sec = material_value / 60
            # heartrate_step_for_animation = int(fps/heartrate_per_sec)
            # heatrate_values = np.zeros(shape=(nb_frames//heartrate_step_for_animation, heartrate_step_for_animation))
            # # heatrate_values[::heartrate_step_for_animation] = 1
            # heartrate_half_step = heartrate_step_for_animation//2 + 1
            # modulo_hr_half_step = heartrate_step_for_animation%2
            # first_half_step_values = np.logspace(0, -2, num=heartrate_half_step)
            # second_half_step_values = np.logspace(-2, 0, num=heartrate_half_step)
            # # second_half_step_values = np.logspace(0, -1, base=np.exp(2), num=heartrate_half_step)

            # smooth_heartrate_step = np.append(first_half_step_values[:heartrate_half_step - 1 + modulo_hr_half_step], second_half_step_values[:-1])
            # # smooth_heartrate_step = np.append(first_half_step_values[1:], second_half_step_values[1:])
            # # heatrate_values = heatrate_values.reshape((len(heatrate_values)//heartrate_step_for_animation, heartrate_step_for_animation))
            # heatrate_values[:] = smooth_heartrate_step
            # heatrate_values = heatrate_values.reshape(-1)
            # modulo_hr = nb_frames%heartrate_step_for_animation
            # remaining_heartrate_values = np.zeros(modulo_hr)
            # remaining_heartrate_values = first_half_step_values[:modulo_hr]
            # heatrate_values = np.append(heatrate_values, remaining_heartrate_values)

            heatrate_values = get_heartrate_sin_wave(material_value, fps=fps, nb_frames=nb_frames)
        

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


        # get n (nb of frames) evenly spaced z samples
        z_linspace = np.linspace(0, z, nb_frames)
 
        # iterate over z samples
        for frame_nb, sample_z in enumerate(z_linspace):

            # set cube transform properties and add corresponding keyframes
            cube_obj.location[2] = previous_z_linspace[frame_nb] + sample_z/2
            cube_obj.keyframe_insert(data_path="location", frame=frame_nb)
            cube_obj.scale = (1, 1, sample_z)
            cube_obj.keyframe_insert(data_path="scale", frame=frame_nb)

            # set material value with values from simulated hearbeat and add keyframe
            # ps_material.node_tree.nodes[ps_shader.name].inputs["Strength"].default_value = simulated_heartrates[frame_nb]
            ps_material.node_tree.nodes[ps_shader.name].inputs["Strength"].default_value = heatrate_values[frame_nb]
            ps_material.node_tree.nodes[ps_shader.name].inputs["Strength"].keyframe_insert("default_value", frame=frame_nb)
        
        # add y samples to previous z samples to get the total z values per frame
        previous_z_linspace += z_linspace

    
    ## 3. Update z labels if show labels enabled

    # if show labels enabled
    if show_labels:

        # iterate over frame numbers
        for frame_nb in range(nb_frames):

            # set y label text transform properties and add corresponding keyframes
            z_text_obj.location[2] = previous_z_linspace[frame_nb] + label_location_offset
            z_text_obj.keyframe_insert(data_path="location", frame=frame_nb)


        previous_z_linspace = [f"{y:.2f} {z_label_prefix}" for y in previous_z_linspace]

        # update text
        @persistent
        def update(scene):
            # blender_utils.update_text_handler(scene, z_text_obj, np.around(previous_z_linspace, decimals=2))
            blender_utils.update_text_handler(scene, z_text_obj, previous_z_linspace)
        
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
blender_utils.clean_scene()

# # set scene frame start and end 
# blender_utils.set_scene_frame_range(bpy.context.scene, frame_start=FRAME_START, frame_end=FRAME_END)

# # set dark world
# blender_utils.set_default_world(color_rgba=(0,0,0,1))

# # set render settings
# blender_utils.set_default_eevee_render_settings()

# set default settings
blender_utils.set_default_settings()

# create collection
parent_collection = blender_utils.create_collection("Collection")

# =====================================================================
# Read data
# =====================================================================

# read csv file into pandas dataframe
df = pd.read_csv("/Users/derrickvanfrausum/BeCode_AI/git-repos/coding-art/core/assets/data/garmin_data/Activities_20210304_20221027_cleaned_grouped_all_days.csv")

# get list of dates (without duplicates) and sort it
# dates = df["Date_yy-mm-dd"].unique()[:3]
dates = df["Date_yy-mm-dd"].unique()
dates.sort()

# normalize calories_series to range of hue values [0,179] (toDo: add normalization to preprocessing data)
df.Calories = data_utils.normalize_between_range(df.Calories, 0, 179)
df["Avg HR"] = data_utils.normalize_between_range(df["Avg HR"], 0, 179)
df["Time"] = data_utils.normalize_between_range(df["Time"], 0,20)

# =====================================================================
# Create animation
# =====================================================================

# iterate over activity date
for bar_center_location_x, activity_date in enumerate(dates):

    # get activities times for current date
    activities_times = df.loc[df["Date_yy-mm-dd"] == activity_date, "Time"]

    # get bar xy location
    xys = df.loc[df["Date_yy-mm-dd"] == activity_date, "grid_coords_xy"]

    
    # get average heart rates and calories for current date (to use their values as modifier or material properties)
    average_hr_series = df.loc[df["Date_yy-mm-dd"] == activity_date, "Avg HR"]
    calories_series = df.loc[df["Date_yy-mm-dd"] == activity_date, "Calories"]

    z_dict = {
        "material": average_hr_series,
        "modifier": calories_series
    }
    

    # create animated bar
    create_animated_bar(
        activities_times.values, activity_date, xys,
        bar_collection_name="Cube_collection",
        bar_default_size=CUBE_SIZE,
        # nb_frames=30, 
        frame_start=FRAME_START,
        frame_end=FRAME_END,
        fps=30,
        show_labels=True,
        z_label_collection_name="Z_label_collection",
        x_label_collection_name="X_label_collection",
        parent_label_collection_name="Label_collection",
        z_label_prefix="s",
        z_dict=z_dict,
        wireframe=True
        )