import bpy


class STARTER_PT_main_panel(bpy.types.Panel):
    bl_idname = "STARTER_PT_main_panel"
    bl_label = "Starter Tools"
    bl_category = "Starter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(text="Blender Plugin Starter")
        layout.operator("starter.add_marker_cube", icon="CUBE")
