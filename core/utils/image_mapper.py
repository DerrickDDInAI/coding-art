"""
Local module to
- find best matching image for region of interest of another image
- find best matching pixel for region of interest (a pixel) of another image

Idea:
- try to use special methods if useful
"""
# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from typing import List, Set, Dict, TypedDict, Tuple, Optional, Union

# import 3rd-party modules
import numpy as np
from numba import njit 

# import local modules

# =====================================================================
# Define functions
# =====================================================================

