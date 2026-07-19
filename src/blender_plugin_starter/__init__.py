bl_info = {
    "name": "Blender Plugin Starter",
    "author": "Your Name",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Starter",
    "description": "A small starter template for building Blender add-ons.",
    "category": "3D View",
}

from .registration import register, unregister


__all__ = ("register", "unregister")
