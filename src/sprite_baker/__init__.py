bl_info = {
    "name": "精灵烘焙",
    "author": "jiahao27",
    "version": (0, 1, 0),
    "blender": (5, 2, 0),
    "location": "视图3D > 侧栏 > 精灵烘焙",
    "description": "将 3D 物体和动画批量烘焙为适配 Unity 的 2D 精灵通道。",
    "category": "导入-导出",
}

def register():
    from .registration import register as register_classes

    register_classes()


def unregister():
    from .registration import unregister as unregister_classes

    unregister_classes()


__all__ = ("register", "unregister")
