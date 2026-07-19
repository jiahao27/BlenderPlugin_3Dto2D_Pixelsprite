# Sprite Baker 插件开发说明

## 基本原则

- 插件入口必须是一个 Python 包，并在 `__init__.py` 中提供 `bl_info`、`register()` 和 `unregister()`。
- 当前目标版本以 `Blender 5.2.0 LTS` 为准。
- 与 Blender UI 相关的类通常继承 `bpy.types.Operator`、`bpy.types.Panel`、`bpy.types.AddonPreferences`。
- 所有注册类统一放在 `registration.py` 中，避免多个文件互相注册导致顺序混乱。
- 打包时 zip 内第一层目录必须是插件包目录，例如 `sprite_baker/__init__.py`。

## 推荐开发流程

1. 在 `src/sprite_baker` 下新增模块。
2. 将新的 Blender 注册类加入 `registration.py` 的 `CLASSES`。
3. 运行 `python scripts/package_addon.py`。
4. 在 Blender 中安装 `dist/blender_plugin_starter.zip`。
5. 修改后重新打包，并在 Blender 的 Add-ons 页面禁用/启用插件测试注册逻辑。

## 需要 Blender 路径时

当前已确认 Blender 路径：

```text
E:\stream\steamapps\common\Blender\blender.exe
```

可以运行下面的命令做 Blender 后台注册检查：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_blender_check.ps1
```

真实导出 smoke test：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_blender_smoke_test.ps1
```

后续还可以继续补充：

- 自动复制插件到 Blender 用户插件目录的脚本。
- 使用 `blender.exe --background --python ...` 执行注册测试。
- 针对具体 Blender 版本的 API 兼容检查。
