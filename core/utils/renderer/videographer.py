"""
Program to define the function to create video using list of saved images in given directory and/or subdirectory
or list
ToDo: create a class renderer to handle video and gif creation
"""
# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from typing import List, Set, Dict, TypedDict, Tuple, Optional, Union, Callable
from pathlib import Path
from uuid import uuid4
from random import shuffle

# import 3rd-party modules
import cv2
from grpc import Call
from imageio import get_writer

# import local modules
from core.utils.renderer.get_resize_interpolation import get_interpolation
from core.utils.renderer.resizer import resize_with_crop, resize_with_pad

# =====================================================================
# Define functions
# =====================================================================

def create_video(
    img_dir:Optional[str]=None,
    img_path_list:List[str]=None,
    out_path:Optional[str]=None,
    codec='MP4V',
    fps=25,
    img_extensions:Set[str]={'.png', '.jpg', '.jpeg'},
    glob_exp:str="**/*",
    sort_img_list:bool=True,
    reverse_img_list:bool=False,
    shuffle_img_list:bool=False,
    duplicate_start_img_amount:int=0,
    duplicate_end_img_amount:int=0,
    out_img_shape:Optional[Tuple[int]]=None,
    resize_fct:Optional[Callable]=None,
    # out_img_scale:Optional[Tuple[int]]=None
    ):
    """
    Function to create video using list of saved images in given directory and/or subdirectory
    or list
    """
    # if list of image paths is not given
    if img_path_list is None:
        # initialize list
        img_path_list = []

    if img_dir is not None:
        # convert img_dir to Path
        img_dir = Path(img_dir)

        # get list of images in img directory and extend to img path list
        img_path_list.extend([str(img_path) for img_path in img_dir.glob(glob_exp) if img_path.suffix in img_extensions])
        
    # if sort_img_list is true and shuffle_img_list false, sort image paths list
    if sort_img_list and not shuffle_img_list:
        img_path_list = sorted(img_path_list, reverse=reverse_img_list)

    # if shuffle_img_list is true, shuffle img path list
    elif shuffle_img_list:
        shuffle(img_path_list)

    # get number of image paths
    nb_imgs = len(img_path_list)

    # get shape of first image in list (if no output shape provided, the shape of first image will be the output shape)
    img_height, img_width, img_channel = cv2.imread(img_path_list[0]).shape

    # # if out_img_scale is provided, unpack it
    # if out_img_scale is not None:
    #     out_img_scale_fy, out_img_scale_fx = out_img_scale
    # else:
    #     out_img_scale_fy, out_img_scale_fx = (None, None)

    # get best interpolation or get none if no resize needed
    # interpolation = get_interpolation((source_img_height, source_img_width), out_img_shape=out_img_shape, out_img_scale=out_img_scale)
    interpolation = get_interpolation((img_height, img_width), out_img_shape=out_img_shape)
    
    # if resize needed, update img_height, img_width
    if interpolation is not None:
        img_height, img_width, img_channel = out_img_shape

    # if output path is not given, set gif filename with a random unique identifier
    if out_path is None:
        # generate a random uuid and convert it to string
        out_path = f"{uuid4()}.{codec[:-1]}"
    

    # create a videoWriter object
    fourcc = cv2.VideoWriter_fourcc(*codec)
    out_video = cv2.VideoWriter(filename=out_path, fourcc=fourcc, fps=fps, frameSize=(img_width, img_height))

    # iterate over the images to add frame to gif
    for img_nb, img_path in enumerate(img_path_list, start=1):
        img = cv2.imread(img_path)
        if resize_fct is not None:
            img = resize_fct(img=img, ref_img_shape=(img_height, img_width, img_channel))

        else:
            # get best interpolation or get none if no resize needed
            # interpolation = get_interpolation((source_img_height, source_img_width), out_img_shape=out_img_shape, out_img_scale=out_img_scale)
            interpolation = get_interpolation((img_height, img_width), out_img_shape=img.shape[:2])

            # if needed, resize image
            if interpolation is not None:
                # img = cv2.resize(img, out_img_shape, fx=out_img_scale_fx, fy=out_img_scale_fy, interpolation=interpolation)
                img = cv2.resize(img, (img_width, img_height), interpolation=interpolation)

        # write several frames for beginning and ending
        if img_nb == 1:
            for _ in range(duplicate_start_img_amount):
                out_video.write(img)
        
        if img_nb == nb_imgs:
            for _ in range(duplicate_end_img_amount):
                out_video.write(img)

        # write output frame
        out_video.write(img)

    # release video rendering
    out_video.release()