"""
Blender utilities
Sources:
    - [GitHub - blender_plus_python/video_grid/video_grid_done.py](https://github.com/CGArtPython/blender_plus_python/blob/main/video_grid/video_grid_done.py)
    - [YouTube - remove orphan blocks in Blender](https://youtu.be/3rNqVPtbhzc?t=149)
    - [YouTube - clean scene in Blender](https://youtu.be/3rNqVPtbhzc)
    - [Blender.stackexchange - How to add text in blender using python](https://blender.stackexchange.com/questions/163487/how-to-add-text-in-blender-using-python)
"""
# =====================================================================
# Import modules
# =====================================================================

# import internal modules
# from typing import List, Set, Dict, TypedDict, Tuple, Optional, Union
import time
from random import seed
from math import radians, degrees

# import 3rd-party modules
import bpy
import addon_utils

# import local modules

# =====================================================================
# Define functions
# =====================================================================

def purge_orphans():
    """
    Function to remove all orphan data blocks
    """

    # if blender version is higher or equal to 3.0
    if bpy.app.version >= (3, 0, 0):
        
        # purge orphans with only one call of orphans_purge function
        bpy.ops.outliner.orphans_purge(
            do_local_ids=True, do_linked_ids=True, do_recursive=True
        )

    # if blender is lower than 3.0
    else:
        # call purge_orphans() recursively until there are no more orphan data blocks to purge
        result = bpy.ops.outliner.orphans_purge()
        if result.pop() != "CANCELLED":
            purge_orphans()


def clean_scene(clean_viewport=True, clean_collections=True, clean_worlds=True, clean_orphans=True):
    """
    Removing all 
    * objects, 
    * collections, 
    * materials, particles, textures, images, curves, meshes, actions, nodes, 
    * and worlds from the scene
    """

    # if clean viewport is true, clean viewport
    if clean_viewport:

        # if active object, go into object mode
        if bpy.context.active_object is not None: bpy.ops.object.mode_set(mode='OBJECT')

        # make sure none of the objects are hidden from viewport, selection, or disabled
        for obj in bpy.data.objects:
            obj.hide_set(False)
            obj.hide_select = False
            obj.hide_viewport = False

        # select all objects and delete them (just like pressing a + x + d in viewport)
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()


    # if clean collections is true, clean collections
    if clean_collections:
        
        # get all collections
        collection_names = [collection.name for collection in bpy.data.collections]

        # remove the collections
        for collection_name in collection_names:
            bpy.data.collections.remove(bpy.data.collections[collection_name])

    # if clean worlds is true, clean worlds and recreate a new one
    if clean_worlds:

        # get all worlds
        world_names = [world.name for world in bpy.data.worlds]

        # remove the worlds
        for name in world_names:
            bpy.data.worlds.remove(bpy.data.worlds[name])
            
        # create a new world data block
        bpy.ops.world.new()
        bpy.context.scene.world = bpy.data.worlds["World"]

    # if clean orphans is true, clean orphans
    if clean_orphans: purge_orphans()


# def clean_scene(collection=None):
#     """
#     Function to remove all objects collections inside "Collection"
#     """
#     # # select and delete everything on the viewport (to reset)
#     # go into object mode
#     # bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
#     bpy.ops.object.select_all(action='SELECT')
#     bpy.ops.object.delete(use_global=False)

#     # get Collection "Collection" if no collection provided
#     if collection is None:
#         collection = bpy.data.collections['Collection']
    
#     # ## remove and unlink all objects in collection
#     # for collection_obj in collection.all_objects:
#     #         bpy.data.objects.remove(collection_obj, do_unlink=True)

#     # remove all children collections
#     for child_collection in collection.children:
#             bpy.data.collections.remove(child_collection)


def create_collection(name, parent_collection=None):
    """
    Function to create a child collection
    in active collection or in parent collection if provided
    """
    
    # add new collection to the main database
    collection = bpy.data.collections.new(name=name)
    
    # link new collection to active collection or parent collection if provided
    if parent_collection is None:
        parent_collection = bpy.context.collection
    
    parent_collection.children.link(collection)

    return collection


def set_default_eevee_render_settings():
    """
    Function to set better default settings for Eevee engine
    """
    
    # set convenient variable
    scene = bpy.context.scene

    # set Eevee engine
    scene.render.engine = 'BLENDER_EEVEE'

    # set eevee properies
    scene.eevee.taa_render_samples = 64

    scene.eevee.use_gtao = True # ambient occlusion
    scene.eevee.gtao_distance = 4
    scene.eevee.gtao_factor = 5

    scene.eevee.use_bloom = True
    scene.eevee.bloom_intensity = 0.005

    scene.eevee.use_bokeh_high_quality_slight_defocus = True
    scene.eevee.use_ssr = True
    scene.eevee.use_shadow_high_bitdepth = True
    scene.view_settings.look = 'Very High Contrast'


def set_output_properties(
    filepath="/tmp/",
    file_format="PNG",
    resolution_x=1920, 
    resolution_y=1080, 
    fps=30, 
    frame_start=1,
    frame_end=300
    ):
    """
    Function to set the output properties
    """
    # set convenient variable
    scene = bpy.context.scene

    # set output properties
    scene.render.resolution_x = resolution_x
    scene.render.resolution_y = resolution_y
    scene.render.fps = fps
    scene.frame_start = frame_start
    scene.frame_end = frame_end
    scene.frame_current = scene.frame_start

    scene.render.filepath = filepath
    scene.render.image_settings.file_format = file_format

    # if video render, set output video properties
    if file_format == "FFMPEG":
        scene.render.ffmpeg.format = 'MPEG4'
        scene.render.ffmpeg.constant_rate_factor = 'PERC_LOSSLESS'


def set_default_world(color_rgba=(0,0,0,1)):
    """
    Function to set default world
    """
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs["Color"].default_value = color_rgba


def set_default_settings(
    eevee_render_kwargs=None, 
    output_properties_kwargs=None, 
    world_kwargs=None,
    camera_kwargs=None,
    light_kwargs=None
    ):
    """
    Function to set default settings
    """
    # if set empty dictionary when dict of arguments is none to call functions with default args 
    if eevee_render_kwargs is None: eevee_render_kwargs = {}
    if output_properties_kwargs is None: output_properties_kwargs = {}
    if world_kwargs is None: world_kwargs = {}
    if camera_kwargs is None: camera_kwargs = {}
    if light_kwargs is None: light_kwargs = {}

    # set default settings
    set_default_eevee_render_settings(**eevee_render_kwargs)
    set_output_properties(**output_properties_kwargs)
    set_default_world(**world_kwargs)

    # add camera and light objects
    add_camera(**camera_kwargs)
    add_light(**light_kwargs)


# def set_scene_frame_range(scene, frame_start = 0, frame_end = 30):
#     """
#     Function to set scene frame start and end
#     """
#     scene.frame_start = frame_start
#     scene.frame_end = frame_end


def activate_object(obj):
    """
    Function to activate object
    """

    # deselect all objects in viewport
    bpy.ops.object.select_all(action="DESELECT")

    # select only the object in viewport
    obj.select_set(True)

    # activate object in outliner
    bpy.context.view_layer.objects.active = obj


def add_text(text: str, obj_name=None, collection=None):
    """
    Function to add text to the scene
    """
    
    # set object name to text string if not provided
    # obj_name = text if obj_name is None else obj_name
    obj_name = obj_name or text
    
    # create new font curve (i.e text)
    font_curve = bpy.data.curves.new(type="FONT", name=obj_name)

    # edit text
    font_curve.body = text

    # create font object from text
    font_obj = bpy.data.objects.new(name=obj_name, object_data=font_curve)

    # link font object to active collection or "Collection"
    if collection is None:
        # collection = bpy.data.collections['Collection']
        collection = bpy.context.collection

    collection.objects.link(font_obj)

    return font_obj


def update_text_handler(scene, text_obj, text_values_per_frame):
    """
    Function to update text value.
    Usage:
    from bpy.app.handlers import persistent

    @persistent
    def update(scene):
        blender_utils.update_text_handler(scene, text_obj, text_values_per_frame)
    
    bpy.app.handlers.frame_change_pre.append(update)
    """
    current_frame = scene.frame_current
    text_obj.data.body = f"{text_values_per_frame[current_frame]}"


def add_material(material_name: str):
    """
    Function to create a material
    """

    # get material if exists or else none
    material = bpy.data.materials.get(material_name)

    # if no material, create a new one
    if material is None:
        material = bpy.data.materials.new(name=material_name)
        
    # enable nodes
    material.use_nodes = True
    
    # if node tree already exists,
    # clear all links and nodes to start
    if material.node_tree:
        material.node_tree.links.clear()
        material.node_tree.nodes.clear()

    return material


def add_shader(material_name, type='ShaderNodeBsdfPrincipled', settings_dict=None):
    """
    Function to add a shader to the material
    """

    # add material
    material = add_material(material_name=material_name)

    # get nodes and links
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # create output node and set node location
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = 400, 0 # set node location

    # create shader
    shader = nodes.new(type=type)
    node = nodes[shader.name]

    # set shader properties if provided
    if settings_dict is not None:
        for key, value in settings_dict.items():
            node.inputs[key].default_value = value

    # link shader output to output node
    links.new(shader.outputs[0], output_node.inputs[0])

    return material, shader


def set_time_seed():
    """
    Sets random seed based on the time
    and copies the seed into the clipboard
    """
    time_seed = time.time()
    print(f"seed: {time_seed}")
    seed(time_seed)

    # add the seed value to your clipboard
    bpy.context.window_manager.clipboard = str(time_seed)

    return time_seed


def add_empty(name="empty.cntrl"):
    """
    Function to add empty object
    """

    # add empty object
    bpy.ops.object.empty_add(type="PLAIN_AXES", align="WORLD")

    # get active object: empty object
    empty_obj = bpy.context.active_object
    
    # set empty object name
    empty_obj.name = name

    return empty_obj


def track_empty(obj):
    """
    Function to add empty and add a constraint to the object:
    'Track To' this empty
    """

    # add empty object
    empty_obj = add_empty(name=f"empty.tracked_by.{obj.name}")

    # activate tracking object
    activate_object(obj)

    # add constraint: 'track to'
    bpy.ops.object.constraint_add(type="TRACK_TO")

    # set constraint target
    bpy.context.object.constraints["Track To"].target = empty_obj

    return empty_obj


def add_camera(
    location=(0,0,0), rotation=(1.10871, 0.0132652, 1.14827), 
    focal_length=50, 
    passepartout_alpha=0.5,
    track_to_empty=False):
    """
    create and setup the camera
    """

    # add camera
    bpy.ops.object.camera_add(location=location, rotation=rotation)

    # get active object: camera
    camera_obj = bpy.context.active_object

    # set camera as "active camera" in the scene
    bpy.context.scene.camera = camera_obj

    # set focal Length of camera
    camera_obj.data.lens = focal_length

    # set passepartout:
    # darkens area outside of camera’s field of view
    camera_obj.data.passepartout_alpha = passepartout_alpha

    # if track to empty true, add a 'track to' constraint to camera
    if track_to_empty:
        track_empty(camera_obj)

    return camera_obj


def add_light(
    type="SUN",
    radius=1,
    location=(4.07625, 1.00545, 5.90386), rotation=(0, 0.6042797269578053, 0.24183317022218467),
    energy=2,
    specular_factor=0,
    use_shadow=True
    ):
    """
    Function to add light object
    """

    # add light object
    bpy.ops.object.light_add(type=type, radius=radius, location=location, rotation=rotation)

    # get active object: sun
    light_obj = bpy.context.active_object

    # set light properties
    light_obj.data.energy = energy
    light_obj.data.specular_factor = specular_factor
    light_obj.data.use_shadow = use_shadow

    return light_obj


def enable_import_images_as_planes():
    """
    Function to enable import images as planes
    """
    
    # check addon state
    loaded_default, loaded_state = addon_utils.check("io_import_images_as_planes")

    # if addon disabled, enable it 
    if not loaded_state:
        addon_utils.enable("io_import_images_as_planes")

# =====================================================================
# Test functions
# =====================================================================

if __name__ == "__main__":

    # reset scene
    # collection = bpy.data.collections["some_collection_name"]
    # reset_scene(collection)
    # reset_scene()
    clean_scene()
    set_default_settings()

    enable_import_images_as_planes()

    parent_collection = create_collection("Collection")
    collection = create_collection("some_collection_name", parent_collection)
    text_obj = add_text("some_text", obj_name="text_obj_name", collection=collection)