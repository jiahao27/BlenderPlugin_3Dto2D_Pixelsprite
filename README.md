# Blender Plugin Starter

这是一个用于 Blender 插件开发的基础工程。当前模板包含一个可注册的 Blender add-on、示例操作器、示例面板、偏好设置、打包脚本和开发说明。

## 项目结构

```text
.
├── src/
│   └── blender_plugin_starter/   # Blender 可安装插件包
├── scripts/                      # 本地开发、打包、环境探测脚本
├── docs/                         # 开发说明
└── dist/                         # 打包产物，Git 忽略
```

## 快速开始

1. 修改 `src/blender_plugin_starter/__init__.py` 里的 `bl_info`，填入你的插件名称、作者、版本和 Blender 版本要求。
2. 在 Blender 中打开 `Edit > Preferences > Add-ons > Install...`。
3. 运行打包命令生成 zip：

```powershell
python scripts/package_addon.py
```

4. 选择 `dist/blender_plugin_starter.zip` 安装并启用插件。

## 环境状态

- 已在当前机器上找到 Python：可用 `python` 或具体路径运行脚本。
- 当前命令行没有直接识别到 `git`，但常见路径中找到了 Git。仓库会使用找到的 Git 可执行文件初始化。
- 当前命令行没有直接识别到 `blender`。如果需要自动安装、自动启动 Blender 或跑 Blender 内部测试，请提供 `blender.exe` 路径。

## 常用命令

```powershell
# 打包插件 zip
python scripts/package_addon.py

# 探测 Python / Git / Blender
powershell -ExecutionPolicy Bypass -File scripts/find_tools.ps1
```

更多开发建议见 [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)。
