"""
Program to define utility functions
"""
# =====================================================================
# Import modules
# =====================================================================

# import internal modules

# import 3rd-party modules
import numpy as np

# import local modules

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