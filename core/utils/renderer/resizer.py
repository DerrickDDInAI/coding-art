"""
Local module to
- resize image with padding to keep same aspect ratio
- resize image after cropping to keep same aspect ratio
"""
# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from typing import List, Set, Dict, TypedDict, Tuple, Optional, Union

# import 3rd-party modules
import numpy as np
import cv2

# import local modules
from utils.renderer.get_resize_interpolation import get_interpolation

# =====================================================================
# Define functions
# =====================================================================

def resize_with_pad(
    img:Optional[np.array] = None,
    ref_img:Optional[np.array] = None,
    img_path:Optional[str] = None,
    ref_img_path:Optional[str] = None,
    ref_img_shape:Optional[Tuple[int]] = None,
    cvt_color:Optional[int] = None
    ) -> np.array:
    """
    Function to resize image with padding to keep same aspect ratio
    """

    # read image if image path passed
    if img_path is not None:
        img = cv2.imread(img_path)

    if cvt_color is not None:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

    # read ref image if ref image path passed and no image shape passed
    if (ref_img_path is not None) and (ref_img_shape is None):
        ref_img = cv2.imread(ref_img_path)
        ref_img_shape = ref_img.shape

    # get images shapes
    img_height, img_width, img_channel = img.shape
    ref_img_height, ref_img_width, img_channel = ref_img_shape
    
    # print images shapes
    print(f"img: {img_height, img_width}, ref_img: {(ref_img_height, ref_img_width)}")

    # get aspect ratio of both images
    img_ratio = img_width/img_height
    ref_img_ratio = ref_img_width/ref_img_height
    print(f"img_ratio: {img_ratio}, ref_img_ratio: {ref_img_ratio}")

    # if same aspect ratio, no need for padding
    if img_ratio == ref_img_ratio:
        out_img = img

    # else, padding required
    else:

        # if img_ratio is smaller than ref_img_ratio, add padding to width to have the same aspect ratio as reference
        if img_ratio < ref_img_ratio:
            # get new width
            new_width = round(img_height*ref_img_ratio)
            out_img = np.zeros((img_height, new_width, img_channel), dtype=img.dtype)

            # get yx positions to center image
            y, x = 0, (new_width - img_width)//2

        # if img_ratio is smaller than ref_img_ratio, add padding to height to have the same aspect ratio as reference
        else:
            # get new height
            new_height = round(img_width/ref_img_ratio)
            out_img = np.zeros((new_height, img_width, img_channel), dtype=img.dtype)

            # get yx positions to center image
            y, x = (new_height - img_height)//2, 0

        # paste image at the center of black canvas
        out_img[y:y+img_height, x:x+img_width] = img

    # get interpolation
    interpolation = get_interpolation(src_img_shape=img.shape, out_img_shape=(ref_img_height, ref_img_width, img_channel))

    # return resize image with zeros padding (to get the reference ratio) to reference shape
    return cv2.resize(out_img, (ref_img_width, ref_img_height), interpolation=interpolation)


def resize_with_crop(
    img:Optional[np.array] = None,
    ref_img:Optional[np.array] = None,
    img_path:Optional[str] = None,
    ref_img_path:Optional[str] = None,
    ref_img_shape:Optional[Tuple[int]] = None,
    cvt_color:Optional[int] = None
    ) -> np.array:
    """
    Function to resize image after cropping to keep same aspect ratio
    """

    # read image if image path passed
    if img_path is not None:
        img = cv2.imread(img_path)

    if cvt_color is not None:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

    # read ref image if ref image path passed and no image shape passed
    if (ref_img_path is not None) and (ref_img_shape is None):
        ref_img = cv2.imread(ref_img_path)
        ref_img_shape = ref_img

    # get images shapes
    img_height, img_width, img_channel = img.shape
    ref_img_height, ref_img_width, img_channel = ref_img_shape
    
    # print images shapes
    print(f"img: {img_height, img_width}, ref_img: {(ref_img_height, ref_img_width)}")

    # get aspect ratio of both images
    img_ratio = img_width/img_height
    ref_img_ratio = ref_img_width/ref_img_height
    print(f"img_ratio: {img_ratio}, ref_img_ratio: {ref_img_ratio}")

    # if same aspect ratio, no need for cropping
    if img_ratio == ref_img_ratio:
        out_img = img.copy()

    # else, cropping required
    else:

        # if img_ratio is smaller than ref_img_ratio, crop width to have the same aspect ratio as reference
        if img_ratio > ref_img_ratio:
            # get new width
            new_width = round(img_height*ref_img_ratio)

            # get yx positions to center image
            y, x = 0, (img_width - new_width)//2

            # crop image from center
            out_img = img[y:y+img_height, x:x+new_width]

        # if img_ratio is bigger than ref_img_ratio, crop height to have the same aspect ratio as reference
        else:
            # get new height
            new_height = round(img_width/ref_img_ratio)

            # get yx positions to center image
            y, x = (img_height - new_height)//2, 0

            # crop image from center
            out_img = img[y:y+new_height, x:x+img_width]

    # get interpolation
    interpolation = get_interpolation(src_img_shape=img.shape, out_img_shape=(ref_img_height, ref_img_width, img_channel))

    # return resize image (after cropping to get the reference ratio) to reference shape
    return cv2.resize(out_img, (ref_img_width, ref_img_height), interpolation=interpolation)