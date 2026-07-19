import bpy


def _draw_status(layout, context):
    box = layout.box()
    box.label(text=context.scene.sprite_baker_pixel_tools.status_message)


class SBK_PT_pixel_tools(bpy.types.Panel):
    bl_idname = "SBK_PT_pixel_tools"
    bl_label = "像素工具"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "精灵烘焙"
    def draw(self, context):
        _draw_status(self.layout, context)


class SBK_PT_pixel_render(bpy.types.Panel):
    bl_idname = "SBK_PT_pixel_render"
    bl_label = "渲染设置"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "精灵烘焙"
    bl_parent_id = "SBK_PT_pixel_tools"
    def draw(self, context):
        settings = context.scene.sprite_baker_pixel_tools
        layout = self.layout
        layout.operator("sprite_baker.apply_render_settings", text="应用像素渲染设置")
        layout.prop(settings, "resolution_preset", text="分辨率")
        if settings.resolution_preset == "CUSTOM":
            row = layout.row(align=True)
            row.prop(settings, "custom_resolution_x", text="宽")
            row.prop(settings, "custom_resolution_y", text="高")
        layout.label(text=f"当前：{settings.current_resolution_x} x {settings.current_resolution_y} 像素")


class SBK_PT_pixel_cameras(bpy.types.Panel):
    bl_idname = "SBK_PT_pixel_cameras"
    bl_label = "像素相机"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "精灵烘焙"
    bl_parent_id = "SBK_PT_pixel_tools"
    def draw(self, context):
        settings = context.scene.sprite_baker_pixel_tools
        layout = self.layout
        layout.prop(settings, "pixel_camera_type", text="相机类型")
        row = layout.row(align=True)
        op = row.operator("sprite_baker.set_camera_projection", text="正交", depress=settings.camera_projection == "ORTHO")
        op.projection = "ORTHO"
        op = row.operator("sprite_baker.set_camera_projection", text="透视", depress=settings.camera_projection == "PERSP")
        op.projection = "PERSP"
        layout.prop(settings, "iso_camera_distance")
        layout.prop(settings, "camera_ortho_scale")
        layout.operator("sprite_baker.create_selected_pixel_camera", text="创建当前类型相机")
        layout.operator("sprite_baker.update_selected_pixel_camera", text="更新选中相机")
        layout.prop(settings, "grid_opacity")
        layout.operator("sprite_baker.cleanup_grid_images", text="清理网格背景")


class SBK_PT_pixel_viewport_preview(bpy.types.Panel):
    bl_idname = "SBK_PT_pixel_viewport_preview"
    bl_label = "视口预览"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "精灵烘焙"
    bl_parent_id = "SBK_PT_pixel_tools"
    def draw(self, context):
        settings = context.scene.sprite_baker_pixel_tools
        layout = self.layout
        layout.operator("sprite_baker.update_viewport_preview_resolution", text="更新预览缩放")
        layout.prop(settings, "viewport_preview_scale")
        row = layout.row(align=True)
        row.prop(settings, "viewport_preview_offset_x", text="X")
        row.prop(settings, "viewport_preview_offset_y", text="Y")
        layout.operator("sprite_baker.setup_viewport_pixel_preview", text="设置视口预览")
        layout.operator("sprite_baker.remove_viewport_pixel_preview", text="移除视口预览")
        layout.operator("sprite_baker.toggle_viewport_display", text="切换视口辅助线")


class SBK_PT_pixel_outline(bpy.types.Panel):
    bl_idname = "SBK_PT_pixel_outline"
    bl_label = "描边"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "精灵烘焙"
    bl_parent_id = "SBK_PT_pixel_tools"
    def draw(self, context):
        settings = context.scene.sprite_baker_pixel_tools
        layout = self.layout
        layout.prop(settings, "outline_thickness")
        layout.prop(settings, "outline_color")
        layout.prop(settings, "outline_background_color")
        layout.operator("sprite_baker.setup_outline", text="设置描边")
        layout.operator("sprite_baker.remove_outline", text="移除描边")


class SBK_PT_pixel_materials(bpy.types.Panel):
    bl_idname = "SBK_PT_pixel_materials"
    bl_label = "像素材质"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "精灵烘焙"
    bl_parent_id = "SBK_PT_pixel_tools"
    def draw(self, context):
        settings = context.scene.sprite_baker_pixel_tools
        layout = self.layout
        layout.prop(settings, "material_type", text="材质类型")
        layout.prop(settings, "material_assignment_mode", text="赋值方式")
        layout.operator("sprite_baker.create_pixel_material", text="创建像素材质")


CLASSES = (
    SBK_PT_pixel_tools,
    SBK_PT_pixel_render,
    SBK_PT_pixel_cameras,
    SBK_PT_pixel_viewport_preview,
    SBK_PT_pixel_outline,
    SBK_PT_pixel_materials,
)
