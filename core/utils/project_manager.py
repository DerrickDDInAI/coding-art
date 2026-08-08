"""Set up the folders one art project needs, and list its input images.

Why bother?
-----------
A generative-art run typically produces thousands of files: intermediate frames,
a contact sheet, the final video. Scattering those next to the source images
makes the next run pick up its own output as input — the classic "my mosaic is
made of mosaics" bug. ``Project`` gives each run a single root folder with named
sub-folders, created up front, so every script can write to
``project.out_img_dir_dict["frames"]`` instead of hard-coding a path.

Typical use::

    project = Project(
        project_dir="outputs/mosaic_2024",
        in_img_dir="tiles",           # relative to project_dir by default
        out_img_dir_list=["frames", "final"],
    )
    project.in_img_path_list          # -> every image found in outputs/mosaic_2024/tiles
    project.out_img_dir_dict["frames"]  # -> Path("outputs/mosaic_2024/frames")
"""

# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

# import local modules
from core.utils.image_pather import IMAGE_EXTENSIONS

# =====================================================================
# Define classes
# =====================================================================


class Project:
    """Create and hold the folder layout of a single art project.

    Arguments:
    * project_dir: root folder of the project. Created if it does not exist.
    * in_img_dir: folder holding the input images.
    * in_img_path_list: extra input image paths, added to whatever ``in_img_dir``
      contains. Use it to mix a curated selection with a whole folder.
    * out_img_dir_list: names of the output sub-folders to create.
    * parents: create missing intermediate folders (``mkdir -p`` behaviour).
    * exist_ok: do not raise when a folder already exists — the normal case when
      you re-run a project.
    * in_project_dir: interpret ``in_img_dir`` and ``out_img_dir_list`` as
      relative to ``project_dir``. Set to ``False`` to read inputs from a shared
      library that lives elsewhere on disk.
    * **get_img_path_args: forwarded to :meth:`get_img_path_list`
      (``img_extensions``, ``glob_exp``, ``sort_img_list``, ``reverse_img_list``).

    Attributes:
    * project_dir: ``Path`` to the project root.
    * in_img_dir: ``Path`` to the input folder, or ``None``.
    * in_img_path_list: sorted list of input image paths, as strings.
    * out_img_dir_dict: maps a folder *name* to its full ``Path``, so scripts can
      look a folder up by name instead of rebuilding the path.
    """

    def __init__(
        self,
        project_dir: Union[str, Path],
        in_img_dir: Optional[Union[str, Path]] = None,
        in_img_path_list: Optional[List[str]] = None,
        out_img_dir_list: Optional[List[Union[str, Path]]] = None,
        parents: bool = True,
        exist_ok: bool = True,
        in_project_dir: bool = True,
        **get_img_path_args,
    ) -> None:
        # accept a plain string as well as a Path everywhere
        self.project_dir: Path = Path(project_dir)

        # maps folder name -> full path; filled in by make_dir below
        self.out_img_dir_dict: Dict[str, Path] = {}

        # create the project root first: every other folder lives inside it
        self.make_dir(
            self.project_dir,
            parents=parents,
            exist_ok=exist_ok,
            in_project_dir=False,
            is_project_dir=True,
        )

        # copy the caller's list instead of storing the object they passed:
        # we are about to extend it, and mutating a caller's list is a nasty surprise
        self.in_img_path_list: List[str] = list(in_img_path_list) if in_img_path_list else []

        self.out_img_dir_list: List[Union[str, Path]] = list(out_img_dir_list) if out_img_dir_list else []

        # create every requested output folder up front, so a long render never
        # dies at frame 900 because a folder was missing
        for out_img_dir in self.out_img_dir_list:
            self.make_dir(out_img_dir, parents=parents, exist_ok=exist_ok, in_project_dir=in_project_dir)

        # resolve the input folder, relative to the project root unless told otherwise
        self.in_img_dir: Optional[Path] = None
        if in_img_dir is not None:
            self.in_img_dir = (self.project_dir / in_img_dir) if in_project_dir else Path(in_img_dir)

        # finally, list the images this project will read
        self.in_img_path_list = self.get_img_path_list(
            img_dir=self.in_img_dir,
            img_path_list=self.in_img_path_list,
            **get_img_path_args,
        )

    def __repr__(self) -> str:
        return (
            f"Project(project_dir={str(self.project_dir)!r}, "
            f"inputs={len(self.in_img_path_list)}, "
            f"output_dirs={sorted(self.out_img_dir_dict)})"
        )

    def make_dir(
        self,
        directory: Union[str, Path],
        parents: bool = True,
        exist_ok: bool = True,
        in_project_dir: bool = True,
        is_project_dir: bool = False,
    ) -> Path:
        """Create one folder and register it in :attr:`out_img_dir_dict`.

        Arguments:
        * directory: folder to create.
        * parents: also create any missing parent folder.
        * exist_ok: do nothing (instead of raising) if it already exists.
        * in_project_dir: treat ``directory`` as relative to the project root.
        * is_project_dir: internal flag — the project root itself is not an
          *output* folder, so it is not added to the lookup dictionary.

        Returns: the ``Path`` that was created.
        """
        directory = (self.project_dir / directory) if in_project_dir else Path(directory)

        # parents=True is `mkdir -p`: create the whole chain at once
        directory.mkdir(parents=parents, exist_ok=exist_ok)

        if not is_project_dir:
            # key by folder name so callers can write out_img_dir_dict["frames"]
            self.out_img_dir_dict[directory.name] = directory

        return directory

    @staticmethod
    def get_img_path_list(
        img_dir: Optional[Union[str, Path]] = None,
        img_path_list: Optional[List[str]] = None,
        img_extensions: Iterable[str] = IMAGE_EXTENSIONS,
        glob_exp: str = "**/*",
        sort_img_list: bool = True,
        reverse_img_list: bool = False,
    ) -> List[str]:
        """List the images of ``img_dir``, appended to ``img_path_list``.

        ``glob_exp`` defaults to ``"**/*"`` (search sub-folders too); pass
        ``"*"`` to stay in the top folder only.

        Sorting is on by default because in this repo file order is usually the
        order frames appear in a video — see the note in
        :mod:`core.utils.image_pather`.
        """
        img_path_list = list(img_path_list) if img_path_list else []

        if img_dir is not None:
            img_dir = Path(img_dir)

            # compare suffixes in lowercase so `.JPG` and `.jpg` both match
            wanted_suffixes = {
                ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in img_extensions
            }

            img_path_list.extend(
                str(img_path)
                for img_path in img_dir.glob(glob_exp)
                if img_path.is_file() and img_path.suffix.lower() in wanted_suffixes
            )

        if sort_img_list:
            img_path_list = sorted(img_path_list, reverse=reverse_img_list)

        return img_path_list
