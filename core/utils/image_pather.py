"""
Local module to get a list of image paths
"""
# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from typing import List, Set, Dict, TypedDict, Tuple, Optional, Union
from pathlib import Path
from random import shuffle

# =====================================================================
# Define functions
# =====================================================================

def get_img_paths(input_dir, extensions={'.png', '.jpg', '.jpeg'}, to_shuffle=False) -> List[str]:
    """
    Function to get a list of image paths
    """

    # convert to Path if input_dir is a string
    if isinstance(input_dir, str):
        input_dir = Path(input_dir)

    # get image paths
    img_paths = [str(image_path) for image_path in input_dir.glob('**/*') if image_path.suffix in extensions]

    # if True, shuffle list
    if to_shuffle:
        shuffle(img_paths)

    return img_paths