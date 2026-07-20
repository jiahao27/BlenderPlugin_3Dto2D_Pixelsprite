import bpy

from .validation import get_active_item


CATEGORY = "精灵烘焙"


class SBK_UL_export_items(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        icon_name = "OUTLINER_OB_MESH" if item.target_type == "OBJECT" else "OUTLINER_COLLECTION"
        layout.prop(item, "name", text="", emboss=False, icon=icon_name)


class SBK_UL_actions(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "action", text="", emboss=False, icon="ACTION")


class SBK_UL_directions(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "name", text="", emboss=False, icon="DRIVER_ROTATIONAL_DIFFERENCE")
        row.prop(item, "angle", text="")


class SBK_PT_project_settings(bpy.types.Panel):
    bl_idname = "SBK_PT_project_settings"
    bl_label = "烘焙模式"
    bl_category = CATEGORY
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        settings = context.scene.sprite_baker_settings
        layout = self.layout
        layout.prop(settings, "bake_mode", expand=True)
        layout.prop(settings, "output_dir")
        layout.prop(settings, "naming_template")
        layout.prop(settings, "merge_atlas")
        row = layout.row(align=True)
        row.prop(settings, "resolution_x")
        row.prop(settings, "resolution_y")
        layout.prop(settings, "pixels_per_unit")


class SBK_PT_camera_frames(bpy.types.Panel):
    bl_idname = "SBK_PT_camera_frames"
    bl_label = "相机与帧范围"
    bl_category = CATEGORY
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "SBK_PT_project_settings"

    def draw(self, context):
        settings = context.scene.sprite_baker_settings
        layout = self.layout
        layout.prop(settings, "camera_mode")
        if settings.bake_mode == "BATCH":
            layout.prop(settings, "camera_source")
        layout.prop(settings, "bake_camera")
        layout.operator("sprite_baker.create_bake_camera", icon="CAMERA_DATA")
        row = layout.row(align=True)
        row.prop(settings, "frame_start")
        row.prop(settings, "frame_end")
        layout.prop(settings, "frame_sampling")
        if settings.frame_sampling == "FRAME_COUNT":
            layout.prop(settings, "bake_frame_count")
        else:
            layout.prop(settings, "frame_step")
        if settings.bake_mode == "CAMERA":
            layout.separator()
            layout.label(text="可选动画绑定")
            layout.prop(settings, "camera_animation_target")
            layout.prop(settings, "camera_action")
        if settings.bake_mode == "BATCH":
            layout.prop(settings, "margin")
            layout.prop(settings, "direction_strategy")
            layout.prop(settings, "batch_framing_mode")


class SBK_PT_export_items(bpy.types.Panel):
    bl_idname = "SBK_PT_export_items"
    bl_label = "烘焙目标"
    bl_category = CATEGORY
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "SBK_PT_project_settings"

    def draw(self, context):
        settings = context.scene.sprite_baker_settings
        item = get_active_item(settings)
        layout = self.layout

        if settings.bake_mode == "CAMERA":
            layout.label(text="相机模式下，导出项是可选的对象过滤器。", icon="INFO")
            layout.label(text="没有导出项时，会烘焙场景中可渲染的网格。")

        row = layout.row()
        row.template_list(
            "SBK_UL_export_items",
            "",
            settings,
            "export_items",
            settings,
            "active_export_item_index",
            rows=3,
        )
        buttons = row.column(align=True)
        buttons.operator("sprite_baker.add_export_item", icon="ADD", text="")
        buttons.operator("sprite_baker.remove_export_item", icon="REMOVE", text="")

        if item is None:
            return

        box = layout.box()
        box.prop(item, "target_type")
        if item.target_type == "OBJECT":
            box.prop(item, "target_object")
        else:
            box.prop(item, "target_collection")

        if settings.bake_mode == "BATCH":
            box.prop(item, "armature")
            box.prop(item, "animation_mode")
            if item.animation_mode == "ACTIONS":
                action_row = box.row()
                action_row.template_list("SBK_UL_actions", "", item, "actions", item, "active_action_index", rows=3)
                action_buttons = action_row.column(align=True)
                action_buttons.operator("sprite_baker.add_action", icon="ADD", text="")
                action_buttons.operator("sprite_baker.remove_action", icon="REMOVE", text="")
                box.prop(item, "use_action_frame_range")
            frame_row = box.row(align=True)
            frame_row.prop(item, "frame_start")
            frame_row.prop(item, "frame_end")
            box.prop(item, "pivot_mode")
            if item.pivot_mode == "CUSTOM":
                box.prop(item, "custom_pivot")
            dir_box = layout.box()
            dir_box.prop(item, "direction_preset")
            if item.direction_preset == "CUSTOM":
                dir_box.prop(item, "custom_directions")
            dir_box.operator("sprite_baker.generate_directions", icon="FILE_REFRESH")
            dir_row = dir_box.row()
            dir_row.template_list("SBK_UL_directions", "", item, "directions", item, "active_direction_index", rows=3)
            dir_row.column(align=True).operator("sprite_baker.remove_direction", icon="REMOVE", text="")


class SBK_PT_pixel_effect(bpy.types.Panel):
    bl_idname = "SBK_PT_pixel_effect"
    bl_label = "像素烘焙效果"
    bl_category = CATEGORY
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "SBK_PT_project_settings"

    def draw(self, context):
        settings = context.scene.sprite_baker_settings
        layout = self.layout
        layout.prop(settings, "enable_pixel_bake")
        col = layout.column(align=True)
        col.enabled = settings.enable_pixel_bake
        col.prop(settings, "pixel_canvas_preset")
        if settings.pixel_canvas_preset == "CUSTOM":
            row = col.row(align=True)
            row.prop(settings, "resolution_x")
            row.prop(settings, "resolution_y")
            col.prop(settings, "pixel_preview_scale")
            row = col.row(align=True)
            row.prop(settings, "pixel_preview_offset_x", text="X")
            row.prop(settings, "pixel_preview_offset_y", text="Y")
        else:
            col.label(text=f"当前画布：{settings.resolution_x} x {settings.resolution_y}")
        col.prop(settings, "pixel_grid_opacity")
        grid_row = layout.row(align=True)
        grid_row.enabled = settings.enable_pixel_bake
        grid_row.operator("sprite_baker.refresh_pixel_grid", text="刷新栅格")
        grid_row.operator("sprite_baker.clear_pixel_grid", text="清理栅格")
        row = layout.row(align=True)
        row.enabled = settings.enable_pixel_bake
        row.operator("sprite_baker.setup_viewport_pixel_preview", text="设置像素预览")
        row.operator("sprite_baker.update_viewport_preview_resolution", text="更新")
        remove_row = layout.row()
        remove_row.enabled = settings.enable_pixel_bake
        remove_row.operator("sprite_baker.remove_viewport_pixel_preview", text="移除像素预览")


class SBK_PT_passes(bpy.types.Panel):
    bl_idname = "SBK_PT_passes"
    bl_label = "通道输出"
    bl_category = CATEGORY
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "SBK_PT_project_settings"

    def draw(self, context):
        settings = context.scene.sprite_baker_settings
        layout = self.layout
        layout.prop(settings, "use_albedo")
        layout.prop(settings, "use_normal")
        layout.prop(settings, "use_mask")
        layout.prop(settings, "unity_names")


class SBK_PT_mask_assignment(bpy.types.Panel):
    bl_idname = "SBK_PT_mask_assignment"
    bl_label = "遮罩分配"
    bl_category = CATEGORY
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "SBK_PT_project_settings"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        if obj is not None:
            layout.label(text=f"物体：{obj.name}")
            draw_mask(layout, obj.sprite_baker_mask)
        mat = obj.active_material if obj is not None else None
        if mat is not None:
            layout.separator()
            layout.label(text=f"材质：{mat.name}")
            draw_mask(layout, mat.sprite_baker_mask)


class SBK_PT_preview_export(bpy.types.Panel):
    bl_idname = "SBK_PT_preview_export"
    bl_label = "预览与导出"
    bl_category = CATEGORY
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "SBK_PT_project_settings"

    def draw(self, context):
        layout = self.layout
        layout.operator("sprite_baker.validate", icon="CHECKMARK")
        layout.operator("sprite_baker.preview", icon="RESTRICT_RENDER_OFF")
        layout.operator("sprite_baker.export", icon="EXPORT")


def draw_mask(layout, mask):
    layout.prop(mask, "enabled", text="启用")
    row = layout.row(align=True)
    row.enabled = mask.enabled
    row.prop(mask, "r", text="R")
    row.prop(mask, "g", text="G")
    row.prop(mask, "b", text="B")
    row.prop(mask, "a", text="A")
