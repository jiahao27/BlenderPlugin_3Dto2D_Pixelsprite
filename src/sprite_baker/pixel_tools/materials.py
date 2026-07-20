from pathlib import Path

import bpy
from bpy.app.handlers import persistent


PALETTE_PATH = Path(__file__).resolve().parents[1] / "assets" / "palettes" / "Pixel_Kit_Color_Palette_Default.png"


def _set_node_input(node, input_name, value):
    socket = node.inputs.get(input_name)
    if socket is not None:
        socket.default_value = value


def _set_enum_if_available(data_block, property_name, value):
    if property_name in data_block.bl_rna.properties:
        try:
            setattr(data_block, property_name, value)
        except TypeError:
            pass


def _load_packed_image(image_path, color_space):
    image = bpy.data.images.load(str(image_path), check_existing=True)
    if hasattr(image, "colorspace_settings"):
        image.colorspace_settings.name = color_space
    if hasattr(image, "alpha_mode"):
        image.alpha_mode = "STRAIGHT"
    if image.packed_file is None:
        image.pack()
    return image


def _load_default_palette_image():
    return _load_packed_image(PALETTE_PATH, "sRGB")


def _create_flat_material():
    material = bpy.data.materials.new("SBK 平面色")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    rgb = nodes.new("ShaderNodeRGB")
    rgb.label = "颜色"
    rgb.outputs["Color"].default_value = (0.8, 0.8, 0.8, 1.0)
    material.node_tree.links.new(rgb.outputs["Color"], output.inputs["Surface"])
    return material


def _create_flat_uv_material():
    material = bpy.data.materials.new("SBK 平面 UV")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    texcoord = nodes.new("ShaderNodeTexCoord")
    image = nodes.new("ShaderNodeTexImage")
    image.image = _load_default_palette_image()
    _set_enum_if_available(image, "interpolation", "Closest")
    _set_enum_if_available(image, "projection", "FLAT")
    _set_enum_if_available(image, "extension", "REPEAT")
    output = nodes.new("ShaderNodeOutputMaterial")
    material.node_tree.links.new(texcoord.outputs["UV"], image.inputs["Vector"])
    material.node_tree.links.new(image.outputs["Color"], output.inputs["Surface"])
    return material


def _create_toon_material():
    material = bpy.data.materials.new("SBK Toon")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    _set_node_input(principled, "Base Color", (0.5, 0.5, 0.5, 1.0))
    _set_node_input(principled, "Metallic", 0.0)
    _set_node_input(principled, "Roughness", 0.5)
    shader_to_rgb = nodes.new("ShaderNodeShaderToRGB")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    output = nodes.new("ShaderNodeOutputMaterial")
    material.node_tree.links.new(principled.outputs["BSDF"], shader_to_rgb.inputs["Shader"])
    material.node_tree.links.new(shader_to_rgb.outputs["Color"], ramp.inputs["Fac"])
    material.node_tree.links.new(ramp.outputs["Color"], output.inputs["Surface"])
    return material


def _create_image_pixel_material():
    material = bpy.data.materials.new("SBK 图片像素化")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    texcoord = nodes.new("ShaderNodeTexCoord")
    image = nodes.new("ShaderNodeTexImage")
    _set_enum_if_available(image, "interpolation", "Closest")
    _set_enum_if_available(image, "projection", "FLAT")
    _set_enum_if_available(image, "extension", "REPEAT")
    output = nodes.new("ShaderNodeOutputMaterial")
    material.node_tree.links.new(texcoord.outputs["UV"], image.inputs["Vector"])
    material.node_tree.links.new(image.outputs["Color"], output.inputs["Surface"])
    return material


def _get_selected_targets(context):
    return [obj for obj in context.selected_objects if hasattr(obj.data, "materials")]


def _assign_material_to_object(obj, material, assignment_mode):
    slots = obj.data.materials
    if assignment_mode == "REPLACE_ACTIVE":
        if not slots:
            slots.append(material)
            obj.active_material_index = len(slots) - 1
            return True
        active_index = min(obj.active_material_index, len(slots) - 1)
        slots[active_index] = material
        obj.active_material_index = active_index
        return True
    slots.append(material)
    obj.active_material_index = len(slots) - 1
    return True


def _assign_material_to_selection(targets, material, assignment_mode):
    assigned = 0
    skipped = 0
    for obj in targets:
        if _assign_material_to_object(obj, material, assignment_mode):
            assigned += 1
        else:
            skipped += 1
    return assigned, skipped


class SBK_OT_create_pixel_material(bpy.types.Operator):
    bl_idname = "sprite_baker.create_pixel_material"
    bl_label = "创建像素材质"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.sprite_baker_pixel_tools
        targets = _get_selected_targets(context)
        if not targets:
            self.report({"WARNING"}, "请先选择可赋予材质的物体。")
            return {"CANCELLED"}
        if settings.material_type == "FLAT":
            material = _create_flat_material()
        elif settings.material_type == "FLAT_UV":
            material = _create_flat_uv_material()
        elif settings.material_type == "TOON":
            material = _create_toon_material()
        else:
            material = _create_image_pixel_material()
        assigned_count, skipped_count = _assign_material_to_selection(targets, material, settings.material_assignment_mode)
        message = f"已创建 {material.name}，并分配给 {assigned_count} 个物体。"
        if skipped_count > 0:
            message += f" 跳过 {skipped_count} 个未支持对象。"
        self.report({"INFO"}, message)
        return {"FINISHED"}


def register_handlers():
    if _refresh_toon_dither_after_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_refresh_toon_dither_after_load)


def unregister_handlers():
    if _refresh_toon_dither_after_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_refresh_toon_dither_after_load)


@persistent
def _refresh_toon_dither_after_load(_dummy):
    return None


CLASSES = (SBK_OT_create_pixel_material,)
