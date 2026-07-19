BPK_OUTLINE_GROUP_NAME = "SBK 描边"
BPK_OUTLINE_GROUP_NODE_NAME = "SBK 描边"
BPK_OUTLINE_DILATE_NODE_NAME = "SBK 描边扩张"
BPK_OUTLINE_MASK_NODE_NAME = "SBK 描边遮罩"
BPK_OUTLINE_COMPOSITE_NODE_NAME = "SBK 描边合成"
BPK_VIEWPORT_OUTLINE_DILATE_NODE_NAME = "SBK 视口描边扩张"
BPK_VIEWPORT_OUTLINE_MASK_NODE_NAME = "SBK 视口描边遮罩"
BPK_VIEWPORT_OUTLINE_COMPOSITE_NODE_NAME = "SBK 视口描边合成"

OUTLINE_NODE_NAMES = (
    BPK_OUTLINE_GROUP_NODE_NAME,
    BPK_OUTLINE_DILATE_NODE_NAME,
    BPK_OUTLINE_MASK_NODE_NAME,
    BPK_OUTLINE_COMPOSITE_NODE_NAME,
    BPK_VIEWPORT_OUTLINE_DILATE_NODE_NAME,
    BPK_VIEWPORT_OUTLINE_MASK_NODE_NAME,
    BPK_VIEWPORT_OUTLINE_COMPOSITE_NODE_NAME,
)


def get_viewport_outline_thickness(render_thickness, preview_resolution):
    if render_thickness <= 0:
        return 0
    return max(1, round(render_thickness / max(0.001, preview_resolution)))


def apply_outline_settings_to_tree(node_tree, outline_thickness, outline_color, background_color, preview_resolution):
    outline_group_node = node_tree.nodes.get(BPK_OUTLINE_GROUP_NODE_NAME)
    if outline_group_node is None or outline_group_node.node_tree is None:
        return False
    outline_group = outline_group_node.node_tree
    pairs = (
        (BPK_OUTLINE_DILATE_NODE_NAME, BPK_OUTLINE_MASK_NODE_NAME, outline_thickness),
        (
            BPK_VIEWPORT_OUTLINE_DILATE_NODE_NAME,
            BPK_VIEWPORT_OUTLINE_MASK_NODE_NAME,
            get_viewport_outline_thickness(outline_thickness, preview_resolution),
        ),
    )
    for dilate_name, mask_name, thickness in pairs:
        dilate_node = outline_group.nodes.get(dilate_name)
        mask_node = outline_group.nodes.get(mask_name)
        if dilate_node and dilate_node.inputs.get("Size"):
            dilate_node.inputs["Size"].default_value = thickness
        if mask_node:
            if mask_node.inputs.get("Background"):
                mask_node.inputs["Background"].default_value = background_color
            if mask_node.inputs.get("Foreground"):
                mask_node.inputs["Foreground"].default_value = outline_color
    return True


def _ensure_group_socket(node_tree, name, in_out, socket_type="NodeSocketColor"):
    if hasattr(node_tree, "interface"):
        for item in node_tree.interface.items_tree:
            if item.item_type == "SOCKET" and item.name == name and item.in_out == in_out:
                return
        node_tree.interface.new_socket(name=name, in_out=in_out, socket_type=socket_type)
        return
    sockets = node_tree.inputs if in_out == "INPUT" else node_tree.outputs
    if name not in sockets:
        sockets.new(socket_type, name)


def _get_socket(sockets, name, fallback_index=0):
    socket = sockets.get(name)
    if socket is not None:
        return socket
    return sockets[fallback_index]


def _replace_input_link(node_tree, input_socket, output_socket):
    for link in list(input_socket.links):
        node_tree.links.remove(link)
    node_tree.links.new(output_socket, input_socket)


def _get_or_create_node(node_tree, node_type, name):
    node = node_tree.nodes.get(name)
    if node is not None and node.bl_idname == node_type:
        return node
    if node is not None:
        node_tree.nodes.remove(node)
    node = node_tree.nodes.new(node_type)
    node.name = name
    node.label = name
    return node


def _configure_dilate_node(dilate_node, outline_thickness):
    if dilate_node.inputs.get("Size"):
        dilate_node.inputs["Size"].default_value = outline_thickness
    if dilate_node.inputs.get("Type"):
        dilate_node.inputs["Type"].default_value = "Steps"


def _configure_alpha_over(node, color=None, background=None):
    if node.inputs.get("Factor"):
        node.inputs["Factor"].default_value = 1.0
    if node.inputs.get("Type"):
        node.inputs["Type"].default_value = "Over"
    if color is not None and node.inputs.get("Foreground"):
        node.inputs["Foreground"].default_value = color
    if background is not None and node.inputs.get("Background"):
        node.inputs["Background"].default_value = background


def _create_outline_branch(group, group_input, group_output, thickness, outline_color, background_color, output_name, y_offset, names):
    dilate = _get_or_create_node(group, "CompositorNodeDilateErode", names[0])
    mask = _get_or_create_node(group, "CompositorNodeAlphaOver", names[1])
    composite = _get_or_create_node(group, "CompositorNodeAlphaOver", names[2])
    _configure_dilate_node(dilate, thickness)
    _configure_alpha_over(mask, outline_color, background_color)
    _configure_alpha_over(composite)
    dilate.location = (-360, y_offset)
    mask.location = (-80, y_offset)
    composite.location = (220, y_offset)
    _replace_input_link(group, _get_socket(dilate.inputs, "Mask"), _get_socket(group_input.outputs, "Alpha", 1))
    _replace_input_link(group, _get_socket(mask.inputs, "Factor", 2), _get_socket(dilate.outputs, "Mask"))
    _replace_input_link(group, _get_socket(composite.inputs, "Background"), _get_socket(mask.outputs, "Image"))
    _replace_input_link(group, _get_socket(composite.inputs, "Foreground", 1), _get_socket(group_input.outputs, "图像", 0))
    _replace_input_link(group, _get_socket(group_output.inputs, output_name, 0), _get_socket(composite.outputs, "Image"))


def ensure_outline_group(outline_thickness, preview_outline_thickness, outline_color, background_color):
    import bpy

    group = bpy.data.node_groups.get(BPK_OUTLINE_GROUP_NAME)
    if group is None or group.bl_idname != "CompositorNodeTree":
        group = bpy.data.node_groups.new(BPK_OUTLINE_GROUP_NAME, "CompositorNodeTree")
    group.nodes.clear()
    _ensure_group_socket(group, "图像", "INPUT")
    _ensure_group_socket(group, "Alpha", "INPUT", "NodeSocketFloat")
    _ensure_group_socket(group, "图像", "OUTPUT")
    _ensure_group_socket(group, "视口图像", "OUTPUT")
    group_input = group.nodes.new("NodeGroupInput")
    group_output = group.nodes.new("NodeGroupOutput")
    _create_outline_branch(
        group,
        group_input,
        group_output,
        outline_thickness,
        outline_color,
        background_color,
        "图像",
        120,
        (BPK_OUTLINE_DILATE_NODE_NAME, BPK_OUTLINE_MASK_NODE_NAME, BPK_OUTLINE_COMPOSITE_NODE_NAME),
    )
    _create_outline_branch(
        group,
        group_input,
        group_output,
        preview_outline_thickness,
        outline_color,
        background_color,
        "视口图像",
        -160,
        (BPK_VIEWPORT_OUTLINE_DILATE_NODE_NAME, BPK_VIEWPORT_OUTLINE_MASK_NODE_NAME, BPK_VIEWPORT_OUTLINE_COMPOSITE_NODE_NAME),
    )
    return group


def setup_outline_nodes(scene, outline_thickness, outline_color, background_color, preview_resolution):
    from .viewport_preview import get_scene_compositor_tree

    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = "RGBA"
    node_tree = get_scene_compositor_tree(scene, create=True)
    if node_tree is None:
        raise RuntimeError("无法创建合成节点。")
    render_layers = _get_or_create_node(node_tree, "CompositorNodeRLayers", "SBK 渲染层")
    group = ensure_outline_group(
        outline_thickness,
        get_viewport_outline_thickness(outline_thickness, preview_resolution),
        outline_color,
        background_color,
    )
    group_node = _get_or_create_node(node_tree, "CompositorNodeGroup", BPK_OUTLINE_GROUP_NODE_NAME)
    group_node.node_tree = group
    _replace_input_link(node_tree, _get_socket(group_node.inputs, "图像", 0), _get_socket(render_layers.outputs, "Image", 0))
    _replace_input_link(node_tree, _get_socket(group_node.inputs, "Alpha", 1), _get_socket(render_layers.outputs, "Alpha", 1))
    if hasattr(scene, "compositing_node_group"):
        output_node = _get_or_create_node(node_tree, "NodeGroupOutput", "SBK 合成输出")
        _ensure_group_socket(node_tree, "图像", "OUTPUT")
        _replace_input_link(node_tree, _get_socket(output_node.inputs, "图像", 0), _get_socket(group_node.outputs, "图像", 0))
    else:
        composite = _get_or_create_node(node_tree, "CompositorNodeComposite", "SBK 最终合成")
        _replace_input_link(node_tree, _get_socket(composite.inputs, "Image", 0), _get_socket(group_node.outputs, "图像", 0))
    return group_node
