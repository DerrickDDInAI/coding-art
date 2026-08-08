"""Shared library used by every project in this repo.

See ``core/utils/README.md`` for the module list and the conventions
(shapes are ``(height, width)``, image reads are checked, frames stream).

Sub-modules are imported explicitly rather than re-exported here, so that
importing one small helper does not pull in OpenCV, imageio and the rest::

    from core.utils.project_manager import Project
    from core.utils.renderer.resizer import resize_with_pad
"""
