"""
Blender utilities
Sources:
    - []()
    - [Blender.stackexchange - How to add text in blender using python](https://blender.stackexchange.com/questions/163487/how-to-add-text-in-blender-using-python)
"""
# =====================================================================
# Import modules
# =====================================================================

# import internal modules
# from typing import List, Set, Dict, TypedDict, Tuple, Optional, Union


# import 3rd-party modules
import bpy

# import local modules

# =====================================================================
# Define functions
# =====================================================================


def reset_scene(collection=None):
    """
    Function to remove all objects collections inside "Collection"
    """
    # # select and delete everything on the viewport (to reset)
    # go into object mode
    # bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # get Collection "Collection" if no collection provided
    if collection is None:
        collection = bpy.data.collections['Collection']
    
    # ## remove and unlink all objects in collection
    # for collection_obj in collection.all_objects:
    #         bpy.data.objects.remove(collection_obj, do_unlink=True)

    # remove all children collections
    for child_collection in collection.children:
            bpy.data.collections.remove(child_collection)


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

def set_scene_frame_range(scene, frame_start = 0, frame_end = 30):
    """
    Function to set scene frame start and end
    """
    scene.frame_start = frame_start
    scene.frame_end = frame_end


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
    Function to update text value
    """
    current_frame = scene.frame_current
    text_obj.data.body = f"{text_values_per_frame[current_frame]}"


# =====================================================================
# Test functions
# =====================================================================

if __name__ == "__main__":

    # reset scene
    # collection = bpy.data.collections["some_collection_name"]
    # reset_scene(collection)
    reset_scene()

    parent_collection = bpy.data.collections["Collection"]
    create_collection("some_collection_name", parent_collection)
    # create_collection("some_collection_name")

    collection = bpy.data.collections['some_collection_name']
    text_obj = add_text("some_text", obj_name="text_obj_name", collection=collection)