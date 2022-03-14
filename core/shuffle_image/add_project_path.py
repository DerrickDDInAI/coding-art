"""
Program to add project lib to path
"""
# =====================================================================
# Import modules
# =====================================================================

# import internal modules
import os.path
from sys import path

# import 3rd-party modules

# import local modules

# =====================================================================
# Define functions
# =====================================================================

# get project module path
module_path = os.path.abspath(os.path.join('..'))

# add module to path if not in there yet
if module_path not in path:
    path.append(module_path)