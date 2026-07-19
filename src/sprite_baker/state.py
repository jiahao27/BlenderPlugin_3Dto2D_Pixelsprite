import bpy


class SceneState:
    def __init__(self, scene, objects):
        self.scene = scene
        self.objects = list(objects)
        self.frame_current = scene.frame_current
        self.camera = scene.camera
        self.render_engine = scene.render.engine
        self.filepath = scene.render.filepath
        self.resolution_x = scene.render.resolution_x
        self.resolution_y = scene.render.resolution_y
        self.film_transparent = scene.render.film_transparent
        self.image_file_format = scene.render.image_settings.file_format
        self.image_color_mode = scene.render.image_settings.color_mode
        self.image_color_depth = scene.render.image_settings.color_depth
        self.view_transform = scene.view_settings.view_transform
        self.look = scene.view_settings.look
        self.exposure = scene.view_settings.exposure
        self.gamma = scene.view_settings.gamma
        self.selected = list(bpy.context.selected_objects)
        self.active = bpy.context.view_layer.objects.active
        self.object_matrices = {obj: obj.matrix_world.copy() for obj in self.objects}
        self.hide_render = {obj: obj.hide_render for obj in bpy.data.objects}
        self.material_slots = {
            obj: [mat for mat in obj.data.materials]
            for obj in self.objects
            if hasattr(obj.data, "materials")
        }
        self.actions = {}
        for obj in self.objects:
            if obj.animation_data:
                self.actions[obj] = obj.animation_data.action

    def restore(self):
        self.scene.frame_set(self.frame_current)
        self.scene.camera = self.camera
        self.scene.render.engine = self.render_engine
        self.scene.render.filepath = self.filepath
        self.scene.render.resolution_x = self.resolution_x
        self.scene.render.resolution_y = self.resolution_y
        self.scene.render.film_transparent = self.film_transparent
        self.scene.render.image_settings.file_format = self.image_file_format
        self.scene.render.image_settings.color_mode = self.image_color_mode
        self.scene.render.image_settings.color_depth = self.image_color_depth
        self.scene.view_settings.view_transform = self.view_transform
        self.scene.view_settings.look = self.look
        self.scene.view_settings.exposure = self.exposure
        self.scene.view_settings.gamma = self.gamma

        for obj, matrix in self.object_matrices.items():
            obj.matrix_world = matrix
        for obj, value in self.hide_render.items():
            if obj.name in bpy.data.objects:
                obj.hide_render = value
        for obj, materials in self.material_slots.items():
            obj.data.materials.clear()
            for mat in materials:
                obj.data.materials.append(mat)
        for obj, action in self.actions.items():
            if obj.animation_data:
                obj.animation_data.action = action

        bpy.ops.object.select_all(action="DESELECT")
        for obj in self.selected:
            if obj.name in bpy.data.objects:
                obj.select_set(True)
        if self.active and self.active.name in bpy.data.objects:
            bpy.context.view_layer.objects.active = self.active


def remove_temp_data(prefix="SBK_TMP_"):
    for obj in list(bpy.data.objects):
        if obj.name.startswith(prefix):
            bpy.data.objects.remove(obj, do_unlink=True)
    for camera in list(bpy.data.cameras):
        if camera.name.startswith(prefix):
            bpy.data.cameras.remove(camera, do_unlink=True)
    for mat in list(bpy.data.materials):
        if mat.name.startswith(prefix):
            bpy.data.materials.remove(mat, do_unlink=True)
