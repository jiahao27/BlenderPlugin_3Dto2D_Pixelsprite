from contextlib import contextmanager

import bpy


def albedo_materials(objects):
    return temporary_materials(objects, lambda _obj, mat: make_albedo_material(mat))


def normal_materials(objects, unity_2d=False, pack_mask=False):
    materials = {}

    def normal_for_slot(obj, mat):
        mask_red = mask_values(obj, mat)[0] if pack_mask else None
        if mask_red not in materials:
            materials[mask_red] = make_normal_material(unity_2d, mask_red)
        return materials[mask_red]

    return temporary_materials(objects, normal_for_slot)


def mask_materials(objects):
    return temporary_materials(objects, lambda obj, mat: make_mask_material(mask_values(obj, mat)))


@contextmanager
def temporary_materials(objects, material_for_slot):
    # Never clear populated mesh slots: Blender would reset face material indices.
    # Object-linked overrides also keep separate assignments on shared meshes.
    overrides = []
    added_slots = []
    try:
        for obj in objects:
            if not hasattr(obj.data, "materials"):
                continue
            if not obj.material_slots:
                obj.data.materials.append(None)
                added_slots.append(obj.data.materials)
            for slot in obj.material_slots:
                replacement = material_for_slot(obj, slot.material)
                original_link = slot.link
                slot.link = "OBJECT"
                overrides.append((slot, original_link, slot.material))
                slot.material = replacement
        yield
    finally:
        for slot, original_link, original_material in reversed(overrides):
            slot.material = original_material
            slot.link = original_link
        for materials in added_slots:
            materials.pop(index=0)


def make_albedo_material(source):
    if source is not None and source.use_nodes:
        mat = source.copy()
        mat.name = f"SBK_TMP_Albedo_{source.name}"
        mat.use_nodes = True
        principled = find_principled(mat)
        output = find_output(mat)
        if principled and output:
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            emission = nodes.new("ShaderNodeEmission")
            emission.inputs["Strength"].default_value = 1.0
            base = principled.inputs.get("Base Color")
            if base and base.is_linked:
                links.new(base.links[0].from_socket, emission.inputs["Color"])
            elif base:
                emission.inputs["Color"].default_value = base.default_value
            links.new(emission.outputs["Emission"], output.inputs["Surface"])
        mat.blend_method = "BLEND"
        return mat

    mat = bpy.data.materials.new("SBK_TMP_Albedo")
    mat.use_nodes = True
    color = source.diffuse_color if source else (1.0, 1.0, 1.0, 1.0)
    set_emission_tree(mat, color)
    mat.blend_method = "BLEND"
    return mat


def make_normal_material(unity_2d=False, mask_red=None):
    mat = bpy.data.materials.new("SBK_TMP_NormalMap")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    geometry = nodes.new("ShaderNodeNewGeometry")
    transform = nodes.new("ShaderNodeVectorTransform")
    transform.vector_type = "NORMAL"
    transform.convert_from = "WORLD"
    transform.convert_to = "CAMERA"
    multiply = nodes.new("ShaderNodeVectorMath")
    multiply.operation = "MULTIPLY"
    # Blender cameras look along local -Z, whereas Unity's 2D Sprite normal
    # maps use +Z for a surface facing the viewer. Keep the legacy output
    # unless the Unity conversion is explicitly requested.
    z_scale = -0.5 if unity_2d else 0.5
    multiply.inputs[1].default_value = (0.5, 0.5, 0.0 if mask_red is not None else z_scale)
    add = nodes.new("ShaderNodeVectorMath")
    add.operation = "ADD"
    add.inputs[1].default_value = (0.5, 0.5, mask_red if mask_red is not None else 0.5)
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Strength"].default_value = 1.0

    links.new(geometry.outputs["Normal"], transform.inputs["Vector"])
    links.new(transform.outputs["Vector"], multiply.inputs[0])
    links.new(multiply.outputs["Vector"], add.inputs[0])
    links.new(add.outputs["Vector"], emission.inputs["Color"])
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return mat


def make_mask_material(values):
    mat = bpy.data.materials.new("SBK_TMP_MaskTex")
    mat.use_nodes = True
    set_emission_tree(mat, values)
    mat.blend_method = "BLEND"
    return mat


def set_emission_tree(mat, color):
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = color
    emission.inputs["Strength"].default_value = 1.0
    links.new(emission.outputs["Emission"], output.inputs["Surface"])


def find_principled(mat):
    for node in mat.node_tree.nodes:
        if node.bl_idname == "ShaderNodeBsdfPrincipled":
            return node
    return None


def find_output(mat):
    for node in mat.node_tree.nodes:
        if node.bl_idname == "ShaderNodeOutputMaterial" and node.is_active_output:
            return node
    return None


def mask_values(obj, mat):
    if mat is not None and mat.sprite_baker_mask.enabled:
        mask = mat.sprite_baker_mask
        return (mask.r, mask.g, mask.b, mask.a)
    if obj.sprite_baker_mask.enabled:
        mask = obj.sprite_baker_mask
        return (mask.r, mask.g, mask.b, mask.a)
    return (0.0, 0.0, 0.0, 0.0)
