import bpy


def setup_albedo(objects):
    mapping = {}
    for obj in objects:
        if not hasattr(obj.data, "materials"):
            continue
        new_mats = []
        for mat in obj.data.materials:
            new_mats.append(make_albedo_material(mat))
        replace_materials(obj, new_mats)
        mapping[obj] = new_mats
    return mapping


def setup_normal(objects, unity_2d=False):
    mat = make_normal_material(unity_2d=unity_2d)
    for obj in objects:
        if hasattr(obj.data, "materials"):
            replace_materials(obj, [mat] * max(1, len(obj.data.materials)))
    return mat


def setup_mask(objects):
    for obj in objects:
        if not hasattr(obj.data, "materials"):
            continue
        new_mats = []
        source_mats = list(obj.data.materials) or [None]
        for mat in source_mats:
            values = mask_values(obj, mat)
            new_mats.append(make_mask_material(values))
        replace_materials(obj, new_mats)


def replace_materials(obj, materials):
    obj.data.materials.clear()
    if not materials:
        materials = [make_albedo_material(None)]
    for mat in materials:
        obj.data.materials.append(mat)


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


def make_normal_material(unity_2d=False):
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
    multiply.inputs[1].default_value = (0.5, 0.5, -0.5) if unity_2d else (0.5, 0.5, 0.5)
    add = nodes.new("ShaderNodeVectorMath")
    add.operation = "ADD"
    add.inputs[1].default_value = (0.5, 0.5, 0.5)
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
