import bpy

from .validation import get_active_item


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
    bl_label = "Project Settings"
    bl_category = "Sprite Baker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        settings = context.scene.sprite_baker_settings
        layout = self.layout
        col = layout.column(align=True)
        col.prop(settings, "output_dir")
        col.prop(settings, "naming_template")
        row = col.row(align=True)
        row.prop(settings, "resolution_x")
        row.prop(settings, "resolution_y")
        col.prop(settings, "pixels_per_unit")
        col.prop(settings, "camera_mode")
        col.prop(settings, "margin")
        col.prop(settings, "frame_step")
        col.prop(settings, "direction_strategy")
        col.prop(settings, "unity_names")


class SBK_PT_export_items(bpy.types.Panel):
    bl_idname = "SBK_PT_export_items"
    bl_label = "Export Items"
    bl_category = "Sprite Baker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "SBK_PT_project_settings"

    def draw(self, context):
        settings = context.scene.sprite_baker_settings
        item = get_active_item(settings)
        layout = self.layout

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
            layout.label(text="Add an item to configure export targets.", icon="INFO")
            return

        box = layout.box()
        box.prop(item, "target_type")
        if item.target_type == "OBJECT":
            box.prop(item, "target_object")
        else:
            box.prop(item, "target_collection")
        box.prop(item, "armature")
        box.prop(item, "animation_mode")

        if item.animation_mode == "ACTIONS":
            action_row = box.row()
            action_row.template_list(
                "SBK_UL_actions",
                "",
                item,
                "actions",
                item,
                "active_action_index",
                rows=3,
            )
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
        dir_row.template_list(
            "SBK_UL_directions",
            "",
            item,
            "directions",
            item,
            "active_direction_index",
            rows=3,
        )
        dir_buttons = dir_row.column(align=True)
        dir_buttons.operator("sprite_baker.remove_direction", icon="REMOVE", text="")


class SBK_PT_passes(bpy.types.Panel):
    bl_idname = "SBK_PT_passes"
    bl_label = "Passes"
    bl_category = "Sprite Baker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "SBK_PT_project_settings"

    def draw(self, context):
        settings = context.scene.sprite_baker_settings
        layout = self.layout
        layout.prop(settings, "use_albedo")
        layout.prop(settings, "use_normal")
        layout.prop(settings, "use_mask")


class SBK_PT_mask_assignment(bpy.types.Panel):
    bl_idname = "SBK_PT_mask_assignment"
    bl_label = "Mask Assignment"
    bl_category = "Sprite Baker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "SBK_PT_project_settings"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        if obj is not None:
            layout.label(text=f"Object: {obj.name}")
            draw_mask(layout, obj.sprite_baker_mask)
        mat = obj.active_material if obj is not None else None
        if mat is not None:
            layout.separator()
            layout.label(text=f"Material: {mat.name}")
            draw_mask(layout, mat.sprite_baker_mask)


class SBK_PT_preview_export(bpy.types.Panel):
    bl_idname = "SBK_PT_preview_export"
    bl_label = "Preview & Export"
    bl_category = "Sprite Baker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "SBK_PT_project_settings"

    def draw(self, context):
        layout = self.layout
        layout.operator("sprite_baker.validate", icon="CHECKMARK")
        layout.operator("sprite_baker.preview", icon="RESTRICT_RENDER_OFF")
        layout.operator("sprite_baker.export", icon="EXPORT")


def draw_mask(layout, mask):
    layout.prop(mask, "enabled")
    row = layout.row(align=True)
    row.enabled = mask.enabled
    row.prop(mask, "r")
    row.prop(mask, "g")
    row.prop(mask, "b")
    row.prop(mask, "a")
