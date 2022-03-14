"""
Program to define the function to create animated gif using list of saved images in given directory and/or subdirectory
or list
"""
# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from typing import List, Set, Dict, TypedDict, Tuple, Optional, Union
from pathlib import Path
from uuid import uuid4

# import 3rd-party modules
import cv2
from imageio import get_writer

# import local modules
from core.utils.get_resize_interpolation import get_interpolation

# =====================================================================
# Define functions
# =====================================================================

def create_gif(
    img_dir:str,
    img_path_list:List[str]=[],
    out_path:Optional[str]=None,
    img_extensions:Set[str]={'.png', '.jpg', '.jpeg'},
    glob_exp:str="**/*",
    sort_img_list:bool=True,
    reverse_img_list:bool=False,
    writer_mode:str='I',
    duplicate_start_img_amount:int=0,
    duplicate_end_img_amount:int=0,
    out_img_shape:Optional[Tuple[int]]=None,
    # out_img_scale:Optional[Tuple[int]]=None
    ):
    """
    Program to create animated animated gif from images in given directory and/or subdirectory
    or list

    Arguments:
    * img_dir: images directory
    * out_path: path where to save the output gif; if None, save gif with a random unique identifier
    * img_extensions: set of extensions to look for in images directory
    * reverse_img_list: boolean to reverse list of images; False by default
    """
    # if image directory provided
    if img_dir is not None:
        # convert img_dir to Path
        img_dir = Path(img_dir)

        # get list of images in img directory and extend to img path list
        img_path_list.extend([str(img_path) for img_path in img_dir.glob(glob_exp) if img_path.suffix in img_extensions])

        # if sort_img_list is True, sort image paths list
        if sort_img_list:
            img_path_list = sorted(img_path_list, reverse=reverse_img_list)

        # get number of image paths
        nb_imgs = len(img_path_list)

    # if output path is not given, set gif filename with a random unique identifier
    if out_path is None:
        # generate a random uuid and convert it to string
        out_path = f"{uuid4()}.gif"

    # write gif within context manager
    with get_writer(out_path, mode=writer_mode) as writer:

        # get shape of first image in list
        source_img_height, source_img_width = cv2.imread(img_path_list[0]).shape[:2]

        # if out_img_shape is provided, unpack it
        if out_img_shape is not None:
            out_img_height, out_img_width = out_img_shape[:2]
        else:
            out_img_height, out_img_width = (None, None)

        # # if out_img_scale is provided, unpack it
        # if out_img_scale is not None:
        #     out_img_scale_fy, out_img_scale_fx = out_img_scale
        # else:
        #     out_img_scale_fy, out_img_scale_fx = (None, None)

        # iterate over the images to add frame to gif
        for img_nb, img_path in enumerate(img_path_list, start=1):
            img = cv2.imread(img_path)

            if out_img_shape is not None:

                # get best interpolation or get none if no resize needed
                # interpolation = get_interpolation((source_img_height, source_img_width), out_img_shape=out_img_shape, out_img_scale=out_img_scale)
                interpolation = get_interpolation((source_img_height, source_img_width), out_img_shape=out_img_shape)
                
                # if needed, resize image
                if interpolation is not None:
                    # img = cv2.resize(img, (out_img_width, out_img_height), fx=out_img_scale_fx, fy=out_img_scale_fy, interpolation=interpolation)
                    img = cv2.resize(img, (out_img_width, out_img_height), interpolation=interpolation)

            # convert image to RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # write several frames for beginning and ending
            if img_nb == 1:
                for _ in range(duplicate_start_img_amount):
                    writer.append_data(img)
            
            if img_nb == nb_imgs - 1:
                for _ in range(duplicate_end_img_amount):
                    writer.append_data(img)

            # write output frame
            writer.append_data(img)