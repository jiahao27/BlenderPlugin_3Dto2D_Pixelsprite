import bpy


class STARTER_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    enable_verbose_logs: bpy.props.BoolProperty(
        name="Enable verbose logs",
        description="Print extra debug information while developing the add-on",
        default=False,
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.prop(self, "enable_verbose_logs")
