# Sprite Baker

Sprite Baker 是一个面向 Blender 5.2 LTS 的多通道 Sprite 烘焙插件，用于把 3D 物体、角色动作或相机画面导出为 Unity 2D/URP 友好的 2D Sprite 资源。

插件界面位于：

```text
视图 3D > 右侧侧栏 > 精灵烘焙
```

## 主要功能

- `相机烘焙`：摄像机看到什么就导出什么，适合固定视角、手动摆相机、像素风预览。
- `批量动作烘焙`：按目标、Action、方向批量导出角色序列帧。
- 多通道输出：`Albedo`、`NormalMap`、`MaskTex`。
- 像素烘焙：支持 `64 x 64`、`128 x 128`、`256 x 256` 画布预设和相机栅格预览。
- 固定动作窗口：批量动作烘焙时先扫描整段动作，使用最大边界固定相机窗口，避免动画大小跳动。
- 合并为大图：导出后可按通道、动作、方向生成 Sprite Sheet，并写入 `metadata.json`。

## 项目结构

```text
.
├── src/
│   └── sprite_baker/             # Blender 可安装插件包
├── scripts/                      # 打包、检查、烟测脚本
├── docs/                         # 开发说明
└── dist/                         # 打包产物，生成 sprite_baker.zip
```

## 打包方法

在仓库根目录运行：

```powershell
python scripts/package_addon.py
```

成功后会生成：

```text
dist/sprite_baker.zip
```

在 Blender 中安装：

```text
Edit > Preferences > Add-ons > Install...
```

选择 `dist/sprite_baker.zip`，安装后启用插件。

## 基本使用

### 相机烘焙

适合“摄像机固定，看到什么导出什么”的工作流。

1. 在 `烘焙模式` 选择 `相机烘焙`。
2. 点击 `创建/更新烘焙相机`，或手动指定 `烘焙相机`。
3. 设置 `起始帧`、`结束帧` 和 `帧采样`。
4. 如果需要烘焙动作，可在 `动画对象` 中选择骨架或物体，在 `动作` 中选择 Action。
5. 选择需要输出的通道：`Albedo`、`NormalMap`、`MaskTex`。
6. 点击 `预览当前帧` 或 `导出精灵序列`。

### 批量动作烘焙

适合角色动作、多方向 Sprite。

1. 在 `烘焙模式` 选择 `批量动作烘焙`。
2. 在 `烘焙目标` 中添加目标物体或集合。
3. 如果是骨骼动画，指定 `骨架`。
4. 选择 `动作模式` 为 `动作`，添加要导出的 Action。
5. 选择方向：`单方向`、`4 向`、`8 向` 或 `自定义`。
6. `构图方式` 推荐使用 `固定动作窗口`，它会扫描整段动作并固定最大相机窗口。
7. 点击 `导出精灵序列`。

### 像素烘焙

在 `像素烘焙效果` 中开启：

```text
启用像素烘焙
```

可选画布：

```text
64 x 64
128 x 128
256 x 256
自定义
```

`刷新栅格` 会在烘焙相机中显示像素格预览；`栅格透明度` 用来调节预览强度。栅格只用于预览，不会写入最终 PNG。

### 合并为大图

在 `项目设置` 中开启：

```text
合并为大图
```

插件会在序列帧导出后，为每个通道分别生成大图：

```text
Albedo_Atlas.png
NormalMap_Atlas.png
MaskTex_Atlas.png
```

合图规则：

```text
16 帧 -> 4 x 4
12 帧 -> 4 x 3
10 帧 -> 5 x 2
17 帧 -> 质数，提示无法合图，只导出序列帧
```

即使没有开启合图，导出前也会检查帧数。如果帧数是质数，会提示之后难以按当前规则合并为大图，但不会阻止导出。

## 输出结构

默认输出结构：

```text
output/
└── item/
    └── action/
        └── direction/
            ├── Albedo/
            ├── NormalMap/
            ├── MaskTex/
            └── metadata.json
```

文件命名遵循：

```text
*_Albedo.png
*_NormalMap.png
*_MaskTex.png
```

合图信息会写入 `metadata.json` 的 `atlas_files` 字段。

## 常用检查命令

```powershell
# Python 语法检查
python -m compileall src scripts

# Blender 后台注册检查
powershell -ExecutionPolicy Bypass -File scripts/run_blender_check.ps1

# Blender 后台导出烟测
powershell -ExecutionPolicy Bypass -File scripts/run_blender_smoke_test.ps1

# 像素工具烟测
powershell -ExecutionPolicy Bypass -File scripts/run_pixel_tools_smoke_test.ps1
```

当前验证 Blender 路径：

```text
E:\stream\steamapps\common\Blender\blender.exe
```

## 推送到 GitHub

当前远端仓库：

```text
git@github.com:jiahao27/BlenderPlugin_3Dto2D_Pixelsprite.git
```

如果本机 `git` 已在 PATH 中：

```powershell
git status
git add .
git commit -m "Update sprite baker"
git push
```

如果 PowerShell 找不到 `git`，可以使用当前机器上的 Git 路径：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' status
& 'C:\Program Files\Git\cmd\git.exe' add .
& 'C:\Program Files\Git\cmd\git.exe' commit -m "Update sprite baker"
& 'C:\Program Files\Git\cmd\git.exe' push
```

如果是第一次连接远端：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' remote add origin git@github.com:jiahao27/BlenderPlugin_3Dto2D_Pixelsprite.git
& 'C:\Program Files\Git\cmd\git.exe' branch -M main
& 'C:\Program Files\Git\cmd\git.exe' push -u origin main
```

## 备注

- 插件目标版本为 Blender 5.2 LTS。
- Unity 适配重点是 2D/URP 的 Sprite Secondary Textures。
- `NormalMap` 和 `MaskTex` 不建议和 `Albedo` 混在同一张图里；插件会分别合图，保证布局一致。
- 图集打包目前是基础 Sprite Sheet 合并，不包含 Unity 自动导入脚本。
