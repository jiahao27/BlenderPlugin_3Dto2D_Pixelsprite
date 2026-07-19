bl_info = {
    "name": "精灵烘焙",
    "author": "jiahao27",
    "version": (0, 1, 0),
    "blender": (5, 2, 0),
    "location": "视图3D > 侧栏 > 精灵烘焙",
    "description": "将 3D 物体和动画批量烘焙为适配 Unity 的 2D 精灵通道。",
    "category": "导入-导出",
}

from .registration import register, unregister


__all__ = ("register", "unregister")
