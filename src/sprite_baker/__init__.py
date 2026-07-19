bl_info = {
    "name": "Sprite Baker",
    "author": "jiahao27",
    "version": (0, 1, 0),
    "blender": (5, 2, 0),
    "location": "View3D > Sidebar > Sprite Baker",
    "description": "Batch bake 3D objects and animations into Unity-ready 2D sprite passes.",
    "category": "Import-Export",
}

from .registration import register, unregister


__all__ = ("register", "unregister")
