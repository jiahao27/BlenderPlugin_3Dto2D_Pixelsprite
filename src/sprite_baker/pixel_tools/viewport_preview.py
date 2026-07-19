import bpy


VIEWPORT_PIXEL_GROUP_NAME = "SBK 视口像素预览"
VIEWPORT_PIXEL_GROUP_NODE_NAME = "SBK 视口像素预览"
VIEWPORT_PIXEL_VIEWER_NODE_NAME = "SBK 视口像素查看器"
VIEWPORT_PIXEL_VALUE_NODE_NAME = "SBK 视口像素缩放"
VIEWPORT_PIXEL_DOWNSCALE_NODE_NAME = "SBK 像素预览降采样"
VIEWPORT_PIXEL_UPSCALE_NODE_NAME = "SBK 像素预览放大"


def get_scene_compositor_tree(scene, create=False):
    if hasattr(scene, "compositing_node_group"):
        node_tree = scene.compositing_node_group
        if node_tree is None and create:
            node_tree = bpy.data.node_groups.new("SBK 合成节点", "CompositorNodeTree")
            scene.compositing_node_group = node_tree
        return node_tree
    if create:
        scene.use_nodes = True
    return getattr(scene, "node_tree", None)


def _ensure_group_socket(node_tree, name, in_out):
    if hasattr(node_tree, "interface"):
        for item in node_tree.interface.items_tree:
            if item.item_type == "SOCKET" and item.name == name and item.in_out == in_out:
                return
        node_tree.interface.new_socket(name=name, in_out=in_out, socket_type="NodeSocketColor")
        return
    sockets = node_tree.inputs if in_out == "INPUT" else node_tree.outputs
    if name not in sockets:
        sockets.new("NodeSocketColor", name)


def _replace_input_link(node_tree, input_socket, output_socket):
    for link in list(input_socket.links):
        node_tree.links.remove(link)
    node_tree.links.new(output_socket, input_socket)


def _get_socket(sockets, name, fallback_index=0):
    socket = sockets.get(name)
    if socket is not None:
        return socket
    return sockets[fallback_index]


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


def _new_node(node_tree, node_types):
    for node_type in node_types:
        try:
            return node_tree.nodes.new(node_type)
        except RuntimeError:
            continue
    raise RuntimeError("无法创建任何视口预览节点。")


def set_viewport_pixel_transform(scene, value, offset_x, offset_y):
    node_tree = get_scene_compositor_tree(scene)
    if node_tree is None:
        return False
    group_node = node_tree.nodes.get(VIEWPORT_PIXEL_GROUP_NODE_NAME)
    if group_node is None or group_node.node_tree is None:
        return False
    group = group_node.node_tree
    value_node = group.nodes.get(VIEWPORT_PIXEL_VALUE_NODE_NAME)
    downscale_node = group.nodes.get(VIEWPORT_PIXEL_DOWNSCALE_NODE_NAME)
    upscale_node = group.nodes.get(VIEWPORT_PIXEL_UPSCALE_NODE_NAME)
    if value_node is None or downscale_node is None or upscale_node is None:
        return False
    value_node.outputs[0].default_value = value
    _set_node_input_default(downscale_node, "X", -offset_x)
    _set_node_input_default(downscale_node, "Y", -offset_y)
    _set_node_input_default(upscale_node, "X", offset_x)
    _set_node_input_default(upscale_node, "Y", offset_y)
    return True


def _configure_transform_node(node):
    for property_name, value in (("filter_type", "NEAREST"), ("interpolation", "NEAREST"), ("extension", "CLIP")):
        if hasattr(node, property_name):
            try:
                setattr(node, property_name, value)
            except TypeError:
                pass


def _ensure_viewport_pixel_group(preview_scale, offset_x=0.0, offset_y=0.0):
    group = bpy.data.node_groups.get(VIEWPORT_PIXEL_GROUP_NAME)
    if group is None or group.bl_idname != "CompositorNodeTree":
        group = bpy.data.node_groups.new(VIEWPORT_PIXEL_GROUP_NAME, "CompositorNodeTree")
    group.nodes.clear()
    _ensure_group_socket(group, "图像", "INPUT")
    _ensure_group_socket(group, "图像", "OUTPUT")
    input_node = group.nodes.new("NodeGroupInput")
    output_node = group.nodes.new("NodeGroupOutput")
    value_node = _new_node(group, ("ShaderNodeValue", "CompositorNodeValue"))
    value_node.name = VIEWPORT_PIXEL_VALUE_NODE_NAME
    value_node.label = "视口预览缩放"
    value_node.outputs[0].default_value = preview_scale
    downscale_node = group.nodes.new("CompositorNodeTransform")
    downscale_node.name = VIEWPORT_PIXEL_DOWNSCALE_NODE_NAME
    downscale_node.label = "像素预览降采样"
    _configure_transform_node(downscale_node)
    _set_node_input_default(downscale_node, "X", -offset_x)
    _set_node_input_default(downscale_node, "Y", -offset_y)
    gamma_node = _new_node(group, ("ShaderNodeGamma", "CompositorNodeGamma"))
    gamma_node.label = "中性占位"
    divide_node = _new_node(group, ("ShaderNodeMath", "CompositorNodeMath"))
    divide_node.operation = "DIVIDE"
    divide_node.inputs[0].default_value = 1.0
    upscale_node = group.nodes.new("CompositorNodeTransform")
    upscale_node.name = VIEWPORT_PIXEL_UPSCALE_NODE_NAME
    upscale_node.label = "像素预览放大"
    _configure_transform_node(upscale_node)
    _set_node_input_default(upscale_node, "X", offset_x)
    _set_node_input_default(upscale_node, "Y", offset_y)
    _replace_input_link(group, _get_socket(downscale_node.inputs, "Image"), _get_socket(input_node.outputs, "图像", 0))
    _replace_input_link(group, _get_socket(downscale_node.inputs, "Scale", 3), value_node.outputs[0])
    _replace_input_link(group, _get_socket(gamma_node.inputs, "Image"), _get_socket(downscale_node.outputs, "Image"))
    _replace_input_link(group, _get_socket(upscale_node.inputs, "Image"), _get_socket(gamma_node.outputs, "Image"))
    _replace_input_link(group, divide_node.inputs[1], value_node.outputs[0])
    _replace_input_link(group, _get_socket(upscale_node.inputs, "Scale", 3), divide_node.outputs[0])
    _replace_input_link(group, _get_socket(output_node.inputs, "图像", 0), _get_socket(upscale_node.outputs, "Image"))
    return group


def setup_viewport_pixel_preview(scene, preview_scale, offset_x=0.0, offset_y=0.0):
    node_tree = get_scene_compositor_tree(scene, create=True)
    if node_tree is None:
        raise RuntimeError("无法创建合成节点。")
    group = _ensure_viewport_pixel_group(preview_scale, offset_x, offset_y)
    group_node = _get_or_create_node(node_tree, "CompositorNodeGroup", VIEWPORT_PIXEL_GROUP_NODE_NAME)
    group_node.node_tree = group
    viewer_node = _get_or_create_node(node_tree, "CompositorNodeViewer", VIEWPORT_PIXEL_VIEWER_NODE_NAME)
    render_layers_node = _get_or_create_node(node_tree, "CompositorNodeRLayers", "SBK 渲染层")
    _replace_input_link(node_tree, _get_socket(group_node.inputs, "图像", 0), _get_socket(render_layers_node.outputs, "图像", 0))
    _replace_input_link(node_tree, _get_socket(viewer_node.inputs, "图像", 0), _get_socket(group_node.outputs, "图像", 0))
    return group


def _set_node_input_default(node, input_name, value):
    socket = node.inputs.get(input_name)
    if socket is not None and hasattr(socket, "default_value"):
        socket.default_value = value
