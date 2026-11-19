# Sprite Baker

**Sprite Baker** 是一款基于 Blender 5.2 LTS 开发的三维模型二维图像自动生成与风格化处理插件。

插件使用 Python 和 Blender Python API（`bpy`）实现三维场景控制、相机管理、动画帧采集及图像导出，并提供像素化处理、多通道烘焙和 Sprite Sheet 合成等功能。

通过将三维模型及其动画数据转换为二维图像序列，Sprite Baker 能够辅助完成多视角视觉素材生成、低分辨率图像制作及风格化资源生产，减少重复性的图像采集与处理工作。

项目主要面向数字媒体艺术、二维动画素材制作、数字视觉设计以及三维数字资产的二维化应用等场景。

## 核心功能

### 1. 三维模型图像生成

- **相机烘焙**：根据指定摄像机的视角生成图像，支持固定视角渲染及手动相机控制。
- **批量动作烘焙**：按照目标物体、动画 Action 和观察方向，批量生成连续帧图像。
- **多方向图像采集**：支持单方向、4 向、8 向及自定义方向配置。
- **动画帧采集**：支持指定起止帧和帧采样间隔，实现动画序列自动生成。
- **固定动作窗口**：扫描完整动画区间，根据最大边界确定相机窗口，避免不同动画帧之间出现画面构图跳动。

### 2. 图像风格化处理

提供面向低分辨率视觉素材的像素化处理功能。

- 支持 `64 × 64`、`128 × 128`、`256 × 256` 等画布预设及自定义分辨率。
- 提供相机像素栅格预览，辅助控制图像构图与像素尺寸。
- 支持目标分辨率直接渲染，以及高分辨率渲染后按块降采样。
- 支持 Albedo 固定调色板映射和标准 K-means 自动颜色量化。

### 3. 多通道图像生成

支持从三维场景中生成不同用途的图像通道：

| 通道 | 说明 |
|---|---|
| `Albedo` | 物体基础颜色信息 |
| `NormalMap` | 法线信息 |
| `MaskTex` | 遮罩信息 |

各通道独立导出，并支持分别合成为图集，便于后续图像处理及数字视觉素材制作。

### 4. 图像序列与图集管理

- 按目标物体、动画动作和观察方向组织输出资源。
- 自动生成连续帧图像序列。
- 支持将图像序列合并为 Sprite Sheet / Atlas。
- 为不同图像通道分别生成图集，保证布局一致。
- 自动生成 `metadata.json`，记录图集相关信息。

## 应用场景

Sprite Baker 不仅可以用于 Sprite 资源制作，也可以作为三维数字资产转化为二维视觉素材的辅助工具。

- **数字媒体艺术与视觉设计**：将三维模型转换为低分辨率图像，为像素艺术、数字插画及风格化视觉创作提供素材。
- **二维动画与动态视觉素材**：通过自动化动画帧采集和多视角渲染，生成连续图像序列，辅助动态视觉内容制作。
- **数字化产品展示**：从不同视角生成产品图像，并进行统一风格处理，用于产品展示、数字目录及视觉资料制作。
- **技术插图与数字文档**：将三维模型转换为多角度二维图像，用于技术说明、产品文档及数字化信息展示。

## 技术方案

| 技术 | 用途 |
|---|---|
| Python | 插件主要开发语言 |
| Blender 5.2 LTS | 三维场景管理与图像渲染平台 |
| Blender Python API (`bpy`) | 场景控制、摄像机管理及动画采集 |
| NumPy（Blender 自带） | 图像重采样和颜色量化 |

系统主要工作流程：

```text
三维模型 / 动画数据
        |
        v
Blender 场景与摄像机控制
        |
        v
多视角渲染 / 动画帧采集
        |
        v
多通道图像生成
        |
        v
像素化与风格化处理
        |
        v
图像序列组织与 Sprite Sheet 合成
        |
        v
PNG 图像 / Atlas / JSON 元数据
```

## 安装方式

### 1. 获取插件

克隆项目仓库：

```bash
git clone git@github.com:jiahao27/BlenderPlugin_3Dto2D_Pixelsprite.git
```

也可以从 GitHub 下载项目压缩包。

### 2. 打包插件

在仓库根目录运行：

```powershell
python scripts/package_addon.py
```

成功后会生成：

```text
dist/
└── sprite_baker.zip
```

### 3. 在 Blender 中安装

打开 Blender，进入：

```text
Edit > Preferences > Add-ons > Install...
```

选择生成的 `dist/sprite_baker.zip`，安装后启用插件。

## 基本使用

插件界面位于：

```text
视图 3D > 右侧侧栏 > 精灵烘焙
```

### 相机烘焙

适合固定视角图像生成，以及手动控制摄像机的工作流程。

1. 在 `烘焙模式` 中选择 `相机烘焙`。
2. 点击 `创建/更新烘焙相机`，或手动指定 `烘焙相机`。
3. 设置 `起始帧`、`结束帧` 和 `帧采样`。
4. 如需采集动画，在 `动画对象` 中选择骨架或物体，并指定对应 Action。
5. 选择需要输出的通道：`Albedo`、`NormalMap`、`MaskTex`。
6. 点击 `预览当前帧` 或 `导出精灵序列`。

### 批量动作烘焙

适合角色动画、多方向图像序列等批量生成场景。

1. 在 `烘焙模式` 中选择 `批量动作烘焙`。
2. 在 `烘焙目标` 中添加目标物体或集合。
3. 如果使用骨骼动画，指定对应的 `骨架`。
4. 在 `动作模式` 中选择 `动作`，并添加需要导出的 Action。
5. 选择图像采集方向：`单方向`、`4 向`、`8 向` 或 `自定义`。
6. `构图方式` 推荐使用 `固定动作窗口`，自动扫描动画区间并确定统一的相机窗口。
7. 点击 `导出精灵序列`。

### 像素化处理

在 `像素烘焙效果` 中开启：

```text
启用像素烘焙
```

支持以下画布预设：

```text
64 x 64
128 x 128
256 x 256
自定义
```

点击 `刷新栅格`，可以在烘焙相机中显示像素网格预览；通过 `栅格透明度` 调整预览效果。

栅格仅用于辅助构图，不会写入最终导出的 PNG 图像。

“空间采样”可选择低采样直接渲染，或高采样后降采样。例如目标画布为 `64 × 64`、倍数为 `4`，就以 `256 × 256` 渲染，最终仍输出 `64 × 64`。高采样在导出时绕过场景合成器；用“预览当前帧”生成实际的降采样结果。

- **Albedo** 可选中心最近邻、左上角、面积平均或颜色众数。中心和左上角采样优先取相应位置，透明时选择最近的可见像素；面积平均在线性颜色空间按 Alpha 加权；众数按块内精确 RGB 值计数。四种模式都按覆盖率计算输出 Alpha。
- **NormalMap** 将 RGB 解码为法线，对有效像素按 Alpha 加权平均后重新归一化，再按线性数据输出。可选的 1 像素扩边仍在最终尺寸上执行。
- **MaskTex** 在高采样时暂不导出；切回低采样即可恢复原设置。

“通道输出 → Albedo 颜色量化”可独立设置，默认关闭：

- **指定调色板**：用逗号或空格分隔六位 HEX 颜色，例如 `#202030, #D28570`，将像素映射到 RGB 空间中最接近的指定颜色。
- **自动调色板 · K-means**：设置颜色数 K、迭代上限和随机种子。算法逐帧学习调色板，最终色数最多为 K；若希望动画各帧使用统一色值，可以选择指定调色板。

颜色量化在空间降采样之后执行，仅改变可见 Albedo 像素的 RGB，保留 Alpha。

### 法线和遮罩通道打包

在「通道输出」启用 `NormalMap`，再勾选「法线通道打包（XY + 遮罩 R）」。该选项默认关闭，当前只支持直接渲染；高采样会输出普通法线图。

| 输出通道 | 数据 |
|---|---|
| R、G | 编码到 0–1 的法线 X、Y |
| B | “遮罩分配”中的 R 权重；优先采用材质设置，其次是物体设置 |
| A | 法线图原有的透明度 |

无需勾选单独的 `MaskTex` 就能打包 R；若需要遮罩中的其他通道，请继续导出独立的 `MaskTex`。打包布局会应用到 NormalMap 帧和图集，`metadata.json` 中会记录 `normal_map_encoding: "XY_MASK_R"`。

在 Unity 中，用 `Default` 类型导入打包图，关闭 sRGB，建议先关闭压缩，避免导入器重新打包颜色通道。由自定义 Shader 读取；`Sprite-Lit-Default` 不会把法线图 B 当作遮罩。样本 `packed` 的解码示例：

```hlsl
float2 xy = packed.rg * 2.0 - 1.0;
float3 normal = normalize(float3(xy, sqrt(saturate(1.0 - dot(xy, xy)))));
float maskR = packed.b;
```

法线重建采用正 Z 半球，原始 Z 的符号不会保留。这是通道打包，可在只需要 R 遮罩时少用一张贴图；PNG 本身仍是 RGBA。

### Sprite Sheet 合成

在 `项目设置` 中开启：

```text
合并为大图
```

插件会在图像序列导出后，按照通道分别生成图集：

```text
Albedo_Atlas.png
NormalMap_Atlas.png
MaskTex_Atlas.png
```

当前图集排列规则：

```text
16 帧 -> 4 x 4
12 帧 -> 4 x 3
10 帧 -> 5 x 2
17 帧 -> 质数，提示无法合图，仅导出序列帧
```

即使未开启图集合成，插件也会在导出前检查帧数，并在无法按照当前规则合成时给出提示，但不会阻止图像序列导出。

## 输出结构

默认输出目录：

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

图像文件命名规则：

```text
*_Albedo.png
*_NormalMap.png
*_MaskTex.png
```

图集文件信息会写入 `metadata.json` 的 `atlas_files` 字段。

## 项目结构

```text
.
├── src/
│   └── sprite_baker/             # Blender 可安装插件包
├── scripts/                      # 打包、检查及测试脚本
├── docs/                         # 开发文档
└── dist/                         # 插件打包产物
```

## 开发与测试

在仓库根目录运行以下命令：

```powershell
# Python 语法检查
python -m compileall src scripts

# 图像算法独立测试（需要 NumPy；也可用 Blender 自带 Python 执行）
python scripts/test_image_processing.py

# Blender 后台注册检查
powershell -ExecutionPolicy Bypass -File scripts/run_blender_check.ps1

# Blender 后台导出烟测
powershell -ExecutionPolicy Bypass -File scripts/run_blender_smoke_test.ps1

# 像素工具烟测
powershell -ExecutionPolicy Bypass -File scripts/run_pixel_tools_smoke_test.ps1
```

## 项目信息

- **项目名称**：Sprite Baker
- **开发语言**：Python
- **运行平台**：Blender 5.2 LTS
- **项目类型**：Blender 插件 / 三维模型二维图像生成与处理工具
- **输出格式**：PNG、Sprite Sheet、JSON

## 备注

- 插件当前目标版本为 Blender 5.2 LTS。
- Unity 适配重点为 2D / URP 的 Sprite Secondary Textures。
- `NormalMap` 和 `MaskTex` 不建议与 `Albedo` 混合在同一张图中；插件会分别生成图集，并保持相同的排列布局。
- 当前图集打包采用基础 Sprite Sheet 合并方式，暂不包含 Unity 自动导入脚本。

