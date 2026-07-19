import bpy


class STARTER_OT_add_marker_cube(bpy.types.Operator):
    """Add a simple cube so the add-on has a visible first action."""

    bl_idname = "starter.add_marker_cube"
    bl_label = "Add Marker Cube"
    bl_description = "Create a cube named Starter Marker"
    bl_options = {"REGISTER", "UNDO"}

    size: bpy.props.FloatProperty(
        name="Size",
        description="Cube size",
        default=1.0,
        min=0.01,
        soft_max=10.0,
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        bpy.ops.mesh.primitive_cube_add(size=self.size)
        cube = context.object
        if cube is not None:
            cube.name = "Starter Marker"
        self.report({"INFO"}, "Starter Marker cube created")
        return {"FINISHED"}
