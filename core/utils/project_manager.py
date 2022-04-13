"""
Local module to manage projects:
- get images paths
- create project output directories

Idea:
- try to use special methods if useful
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

# import local modules

# =====================================================================
# Define classes
# =====================================================================

class Project:
    """
    Class to manage projects
    Arguments:
    * project_dir: string or Path object for project directory. It is required
    * out_img_dir: string or Path object f
    """
    def __init__(
        self,
        project_dir: Union[str,Path],
        in_img_dir:Optional[str] = None,
        in_img_path_list:Optional[List[str]] = None,
        out_img_dir_list: Optional[List[Union[str,Path]]] = None,
        parents: Optional[bool] = True,
        exist_ok: Optional[bool] = True,
        in_project_dir: bool = True,
        **get_img_path_args
    ) -> None:
        """
        Function to create an instance of Project class
        """
        # convert project dir to path if string provided
        self.project_dir = Path(project_dir)

        # if list is none, initialize it
        if in_img_path_list is None:
            self.in_img_path_list = []
        if out_img_dir_list is None:
            self.out_img_dir_list = []

        # iterate over list of output image directory
        for out_img_dir in self.out_img_dir_list:
            self.make_dir(out_img_dir, parents=parents, exist_ok=exist_ok, in_project_dir=in_project_dir)
        
        self.in_img_dir = in_img_dir

        # if input image directory given
        if in_img_dir is not None:
            # if in project dir enabled
            if in_project_dir:
                self.in_img_dir = self.project_dir / in_img_dir
            else:
                self.in_img_dir = Path(in_img_dir)

        # get img paths list
        self.in_img_path_list = self.get_img_path_list(img_dir=self.in_img_dir, img_path_list=self.in_img_path_list, **get_img_path_args)

        # initiate output image directory dictionary
        self.out_img_dir_dict = dict()


    def make_dir(
        self,
        dir: Union[str,Path],
        parents: Optional[bool] = True,
        exist_ok: Optional[bool] = True,
        in_project_dir: bool = True
    ) -> None:
        """
        Function to make directory
        """
        # if create in project dir enabled
        if in_project_dir:
            dir = self.project_dir / dir

        else:
            # just convert dir to path if string provided
            dir = Path(dir)
 
        # create dir if don't exist
        # parents=True to create any intermediate parent dirs if don't exist
        dir.mkdir(parents=parents, exist_ok=exist_ok)

        # add dir to out_img_dir_dict
        self.out_img_dir_dict[dir.name] = dir
    

    @staticmethod
    def get_img_path_list(
        img_dir:Optional[Union[str,Path]]=None,
        img_path_list:Optional[List[str]]=None,
        img_extensions:Set[str]={'.png', '.jpg', '.jpeg'},
        glob_exp:str="**/*",
        sort_img_list:bool=True,
        reverse_img_list:bool=False,
    ) -> List[str]:
        """
        Utility function to get a list of img paths
        """
        # initialize img_path_list if not provided
        if img_path_list is None:
            img_path_list = []

        # if image directory provided
        if img_dir is not None:
            # convert img_dir to path if string provided
            img_dir = Path(img_dir)

            # get list of images in img directory and extend to img path list
            img_path_list.extend([str(img_path) for img_path in img_dir.glob(glob_exp) if img_path.suffix in img_extensions])

        # if sort_img_list is True, sort image paths list
        if sort_img_list:
            img_path_list = sorted(img_path_list, reverse=reverse_img_list)

        return img_path_list