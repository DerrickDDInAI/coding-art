"""
Program to define the function to find the best interpolation mode to resize an image
"""
# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from typing import List, Set, Dict, TypedDict, Tuple, Optional, Union

# import 3rd-party modules
import cv2

# import local modules

# =====================================================================
# Define functions
# =====================================================================

def get_interpolation(src_img_shape, out_img_shape=None, out_img_scale=None):
    """
    Function to get the best interpolation mode to resize an image

    Arguments:
    * src_img_shape: any array type containing source image height, then width (if channel provided, it will be ignored)
    * out_img_shape: any array type containing output image height, then width (if channel provided, it will be ignored)
    * out_img_scale: any array type containing height scale factor first, then width scale factor
    """

    # get source image height & width, and size
    src_img_height, src_img_width = src_img_shape[:2]
    src_img_size = src_img_height * src_img_width

    # by default, no interpolation if no resize operation necessary
    interpolation = None

    # if out_img_shape provided
    if out_img_shape is not None:

        # get output image height & width, and size
        out_img_height, out_img_width = out_img_shape[:2]
        out_img_size = out_img_height * out_img_width
        
        # if provided output image size is bigger than source img or output image shape is the source img shape inverted
        if (out_img_size > src_img_size) or ((out_img_height, out_img_width) == (src_img_height, src_img_width)):
            # set interpolation to cv2.INTER_CUBIC (cv2.INTER_LINEAR should work too, faster but less performing)
            interpolation = cv2.INTER_CUBIC

        # if provided output image size is smaller than source img
        elif out_img_size < src_img_size:
            # set interpolation to cv2.INTER_AREA
            interpolation = cv2.INTER_AREA
        
        # else:
        #     interpolation = None

    # if out_img_shape provided
    if out_img_scale is not None:

        # get height & width scale factors, and total scale factor
        out_img_fy, out_img_fx = out_img_scale
        total_scale_f = out_img_fy * out_img_fx

        # if provided output image scale factor is bigger than 1 (same size as source img)
        if (total_scale_f > 1.0):
            # set interpolation to cv2.INTER_CUBIC (cv2.INTER_LINEAR should work too, faster but less performing)
            interpolation = cv2.INTER_CUBIC

        # if provided output image scale factor is smaller than 1
        elif total_scale_f < 1.0:
            # set interpolation to cv2.INTER_AREA
            interpolation = cv2.INTER_AREA

        # if output image scale factor inverts source img shape
        elif (total_scale_f == 1) and (out_img_fy != 1.0 or out_img_fx != 1.0):
            # set interpolation to cv2.INTER_AREA
            interpolation = cv2.INTER_AREA
        
        # else:
        #     interpolation = None
    
    return interpolation