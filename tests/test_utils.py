"""Tests for the shared library in ``core/utils``.

Run them with::

    pytest

These are deliberately end-to-end: they write real PNGs to a temporary folder and
read back a real MP4 and a real GIF. Image code is full of conventions that only
bite at the boundaries — BGR vs RGB, ``(height, width)`` vs ``(width, height)`` —
and only a round trip through the actual encoder catches those.

``tmp_path`` is a pytest fixture: a fresh empty directory per test, cleaned up
automatically, so tests never interfere with each other or leave files behind.
"""

# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from pathlib import Path

# import 3rd-party modules
import cv2
import imageio
import numpy as np
import pytest

# import local modules
from core.utils.binary_search_tree import BSTNode, build_tree
from core.utils.image_pather import get_img_paths
from core.utils.project_manager import Project
from core.utils.renderer.get_resize_interpolation import get_interpolation
from core.utils.renderer.giffer import create_gif
from core.utils.renderer.resizer import resize_with_crop, resize_with_pad
from core.utils.renderer.videographer import create_video

# =====================================================================
# Define fixtures
# =====================================================================


@pytest.fixture
def frames_dir(tmp_path: Path) -> Path:
    """Six frames that deliberately alternate between landscape and portrait.

    Mixed shapes are the realistic case (photos straight off a phone) and the one
    that breaks naive video code, so it is what the tests use by default.
    """
    frames = tmp_path / "frames"
    frames.mkdir()

    for i in range(6):
        height, width = (120, 200) if i % 2 == 0 else (200, 120)
        img = np.full((height, width, 3), (i * 40, 255 - i * 40, 128), dtype=np.uint8)
        cv2.imwrite(str(frames / f"frame_{i:03d}.png"), img)

    return frames


# =====================================================================
# image_pather
# =====================================================================


def test_get_img_paths_is_sorted_and_complete(frames_dir: Path):
    paths = get_img_paths(frames_dir)

    assert len(paths) == 6
    # sorted order is what makes file order equal frame order
    assert paths == sorted(paths)


def test_get_img_paths_limit(frames_dir: Path):
    assert get_img_paths(frames_dir, limit=2) == get_img_paths(frames_dir)[:2]


def test_get_img_paths_is_case_insensitive(tmp_path: Path):
    """`.JPG` from a camera must be found just like `.jpg`."""
    cv2.imwrite(str(tmp_path / "photo.JPG"), np.zeros((8, 8, 3), dtype=np.uint8))

    assert len(get_img_paths(tmp_path)) == 1


def test_get_img_paths_rejects_a_missing_folder(tmp_path: Path):
    """A typo in a folder name must fail here, not silently return nothing."""
    with pytest.raises(NotADirectoryError):
        get_img_paths(tmp_path / "does_not_exist")


# =====================================================================
# get_resize_interpolation
# =====================================================================


def test_interpolation_none_when_no_resize_needed():
    assert get_interpolation((100, 100), out_img_shape=(100, 100)) is None
    assert get_interpolation((100, 100), out_img_scale=(1.0, 1.0)) is None


def test_interpolation_area_when_shrinking():
    """INTER_AREA averages every source pixel, which is what avoids aliasing."""
    assert get_interpolation((100, 100), out_img_shape=(50, 50)) == cv2.INTER_AREA
    assert get_interpolation((100, 100), out_img_scale=(0.5, 0.5)) == cv2.INTER_AREA


def test_interpolation_cubic_when_growing():
    assert get_interpolation((100, 100), out_img_shape=(200, 200)) == cv2.INTER_CUBIC
    assert get_interpolation((100, 100), out_img_scale=(2.0, 2.0)) == cv2.INTER_CUBIC


def test_interpolation_area_when_one_axis_is_squeezed():
    """Same pixel count, but one axis shrinks — protect it from aliasing."""
    assert get_interpolation((100, 100), out_img_scale=(2.0, 0.5)) == cv2.INTER_AREA


def test_interpolation_rejects_both_targets():
    with pytest.raises(ValueError):
        get_interpolation((10, 10), out_img_shape=(5, 5), out_img_scale=(2, 2))


# =====================================================================
# resizer
# =====================================================================


def test_resize_with_pad_keeps_aspect_ratio_and_adds_bars():
    # a tall white image squeezed into a wide frame must gain black side bars
    tall = np.full((200, 100, 3), 255, dtype=np.uint8)

    out = resize_with_pad(img=tall, ref_img_shape=(100, 300))

    assert out.shape == (100, 300, 3)
    assert out[50, 0].sum() == 0, "left edge should be padding"
    assert out[50, 150].sum() > 0, "centre should be image"


def test_resize_with_crop_fills_the_frame():
    tall = np.full((200, 100, 3), 255, dtype=np.uint8)

    out = resize_with_crop(img=tall, ref_img_shape=(100, 300))

    assert out.shape == (100, 300, 3)
    # cropping keeps content everywhere: no bars
    assert out[50, 0].sum() > 0


def test_resize_honours_cvt_color():
    """Regression: cvt_color used to be ignored and always applied BGR2LAB."""
    img = np.full((200, 100, 3), 255, dtype=np.uint8)

    out = resize_with_pad(img=img, ref_img_shape=(50, 50), cvt_color=cv2.COLOR_BGR2GRAY)

    assert out.shape == (50, 50), "grayscale conversion should drop the channel axis"


def test_resize_raises_on_an_unreadable_file(tmp_path: Path):
    """cv2.imread returns None instead of raising; we must not propagate that."""
    with pytest.raises(FileNotFoundError):
        resize_with_pad(img_path=str(tmp_path / "missing.png"), ref_img_shape=(10, 10))


# =====================================================================
# videographer
# =====================================================================


def test_create_video_frame_count_and_size(frames_dir: Path, tmp_path: Path):
    out_path = create_video(
        img_dir=str(frames_dir),
        out_path=str(tmp_path / "nested" / "out.mp4"),  # the folder does not exist yet
        fps=10,
        out_img_shape=(160, 160),
        resize_fct=resize_with_pad,
        duplicate_start_img_amount=2,
        duplicate_end_img_amount=3,
    )

    capture = cv2.VideoCapture(out_path)
    try:
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    finally:
        capture.release()

    assert (height, width) == (160, 160)
    assert frame_count == 6 + 2 + 3, "held first/last frames should be written too"


def test_create_video_defaults_to_the_first_frame_shape(frames_dir: Path, tmp_path: Path):
    out_path = create_video(img_dir=str(frames_dir), out_path=str(tmp_path / "out.mp4"))

    capture = cv2.VideoCapture(out_path)
    try:
        assert int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) == 6
        assert int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) == 120
    finally:
        capture.release()


def test_create_video_rotation_swaps_the_axes(frames_dir: Path, tmp_path: Path):
    """An odd number of quarter turns turns landscape into portrait."""
    out_path = create_video(img_dir=str(frames_dir), out_path=str(tmp_path / "out.mp4"), rotate_90=1)

    capture = cv2.VideoCapture(out_path)
    try:
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    finally:
        capture.release()

    assert (height, width) == (200, 120)


def test_create_video_rejects_an_empty_input(tmp_path: Path):
    empty = tmp_path / "empty"
    empty.mkdir()

    with pytest.raises(ValueError, match="No frames"):
        create_video(img_dir=str(empty), out_path=str(tmp_path / "out.mp4"))


def test_create_video_rejects_a_malformed_codec(frames_dir: Path, tmp_path: Path):
    """A fourcc is exactly four characters; anything else builds a broken writer.

    Note this only validates the *shape* of the string. Whether a given 4-char
    codec is actually available is a property of your OpenCV build, and is caught
    later by the ``isOpened()`` check.
    """
    with pytest.raises(ValueError, match="fourcc"):
        create_video(img_dir=str(frames_dir), out_path=str(tmp_path / "out.mp4"), codec="H26")


# =====================================================================
# giffer
# =====================================================================


def test_create_gif_frame_count_and_size(frames_dir: Path, tmp_path: Path):
    out_path = create_gif(
        img_dir=str(frames_dir),
        out_path=str(tmp_path / "out.gif"),
        fps=8,
        out_img_shape=(80, 80),
        resize_fct=resize_with_crop,
        optimize_gif=False,
    )

    gif_frames = imageio.mimread(out_path)

    assert len(gif_frames) == 6
    assert gif_frames[0].shape[:2] == (80, 80)


def test_create_gif_converts_bgr_to_rgb(tmp_path: Path):
    """The classic bug: a blue sky coming out orange."""
    blue_dir = tmp_path / "blue"
    blue_dir.mkdir()
    # (255, 0, 0) in BGR is pure blue
    cv2.imwrite(str(blue_dir / "a.png"), np.full((20, 20, 3), (255, 0, 0), dtype=np.uint8))

    out_path = create_gif(img_dir=str(blue_dir), out_path=str(tmp_path / "out.gif"), optimize_gif=False)

    red, _green, blue = imageio.mimread(out_path)[0][10, 10][:3]

    assert blue > 200 and red < 60, "channels look swapped — BGR was written as RGB"


# =====================================================================
# project_manager
# =====================================================================


def test_project_creates_its_output_folders(tmp_path: Path):
    project = Project(project_dir=str(tmp_path / "proj"), out_img_dir_list=["frames", "final"])

    assert set(project.out_img_dir_dict) == {"frames", "final"}
    assert project.out_img_dir_dict["frames"].is_dir()


def test_project_accepts_an_explicit_input_list(frames_dir: Path, tmp_path: Path):
    """Regression: passing in_img_path_list used to raise AttributeError."""
    paths = get_img_paths(frames_dir)[:2]

    project = Project(project_dir=str(tmp_path / "proj"), in_img_path_list=paths)

    assert project.in_img_path_list == sorted(paths)


def test_project_can_read_inputs_from_outside_itself(frames_dir: Path, tmp_path: Path):
    project = Project(
        project_dir=str(tmp_path / "proj"),
        in_img_dir=str(frames_dir),
        in_project_dir=False,
    )

    assert len(project.in_img_path_list) == 6


def test_project_does_not_mutate_the_caller_list(frames_dir: Path, tmp_path: Path):
    paths = get_img_paths(frames_dir)[:2]
    original = list(paths)

    Project(project_dir=str(tmp_path / "proj"), in_img_path_list=paths)

    assert paths == original


# =====================================================================
# binary_search_tree
# =====================================================================


def test_inorder_returns_sorted_values():
    tree = build_tree([30, 10, 40, 20], list("cadb"))

    assert tree.inorder() == [10, 20, 30, 40]


def test_find_closest_returns_the_nearest_neighbour():
    """This is the operation a photo mosaic actually needs."""
    tree = build_tree([10, 20, 30, 40], list("abcd"))

    assert tree.find_closest(31) == (30, "c")
    assert tree.find_closest(29) == (30, "c")
    assert tree.find_closest(0) == (10, "a")  # below every stored value
    assert tree.find_closest(100) == (40, "d")  # above every stored value


def test_exists_reports_exact_matches_only():
    tree = build_tree([10, 20, 30], list("abc"))

    assert tree.exists(20)[0] is True
    assert tree.exists(25)[0] is False


def test_delete_removes_a_value_and_keeps_the_order():
    tree = build_tree([10, 20, 30, 40, 50], list("abcde"), shuffle_first=False)

    tree = tree.delete(20)

    assert tree.inorder() == [10, 30, 40, 50]


def test_delete_keeps_values_and_paths_together():
    """Regression: promoting a successor used to copy its value but not its path."""
    tree = BSTNode(20, "b")
    tree.insert(10, "a")
    tree.insert(30, "c")

    tree = tree.delete(20)

    assert tree.find_closest(30) == (30, "c")


def test_build_tree_rejects_mismatched_inputs():
    with pytest.raises(ValueError):
        build_tree([1, 2], ["only_one"])
