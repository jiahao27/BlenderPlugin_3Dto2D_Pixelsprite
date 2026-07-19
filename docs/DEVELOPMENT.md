# Blender 插件开发说明

## 基本原则

- 插件入口必须是一个 Python 包，并在 `__init__.py` 中提供 `bl_info`、`register()` 和 `unregister()`。
- 与 Blender UI 相关的类通常继承 `bpy.types.Operator`、`bpy.types.Panel`、`bpy.types.AddonPreferences`。
- 所有注册类统一放在 `registration.py` 中，避免多个文件互相注册导致顺序混乱。
- 打包时 zip 内第一层目录必须是插件包目录，例如 `blender_plugin_starter/__init__.py`。

## 推荐开发流程

1. 在 `src/blender_plugin_starter` 下新增模块。
2. 将新的 Blender 注册类加入 `registration.py` 的 `CLASSES`。
3. 运行 `python scripts/package_addon.py`。
4. 在 Blender 中安装 `dist/blender_plugin_starter.zip`。
5. 修改后重新打包，并在 Blender 的 Add-ons 页面禁用/启用插件测试注册逻辑。

## 需要 Blender 路径时

如果后续需要自动化测试或自动安装插件，请提供类似下面的路径：

```text
C:\Program Files\Blender Foundation\Blender 4.2\blender.exe
```

拿到路径后，可以继续补充：

- 自动复制插件到 Blender 用户插件目录的脚本。
- 使用 `blender.exe --background --python ...` 执行注册测试。
- 针对具体 Blender 版本的 API 兼容检查。
