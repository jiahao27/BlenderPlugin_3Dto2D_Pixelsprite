import bpy


VIEWPORT_PIXEL_GROUP_NAME = "SBK Viewport Pixel Preview"
VIEWPORT_PIXEL_GROUP_NODE_NAME = "SBK Viewport Pixel Preview"
VIEWPORT_PIXEL_VIEWER_NODE_NAME = "SBK Viewport Pixel Viewer"
VIEWPORT_PIXEL_COMPOSITE_NODE_NAME = "SBK Pixel Composite"
VIEWPORT_PIXEL_OUTPUT_NODE_NAME = "SBK Pixel Output"
VIEWPORT_PIXEL_VALUE_NODE_NAME = "SBK Viewport Pixel Scale"
VIEWPORT_PIXEL_DOWNSCALE_NODE_NAME = "SBK Pixel Preview Downscale"
VIEWPORT_PIXEL_UPSCALE_NODE_NAME = "SBK Pixel Preview Upscale"


def get_scene_compositor_tree(scene, create=False):
    if hasattr(scene, "compositing_node_group"):
        node_tree = scene.compositing_node_group
        if node_tree is None and create:
            node_tree = bpy.data.node_groups.new("SBK Compositor Nodes", "CompositorNodeTree")
            scene.compositing_node_group = node_tree
        return node_tree
    if create:
        scene.use_nodes = True
    return getattr(scene, "node_tree", None)


def ensure_group_socket(node_tree, name, in_out, socket_type="NodeSocketColor"):
    if hasattr(node_tree, "interface"):
        for item in node_tree.interface.items_tree:
            if item.item_type == "SOCKET" and item.name == name and item.in_out == in_out:
                return
        node_tree.interface.new_socket(name=name, in_out=in_out, socket_type=socket_type)
        return
    sockets = node_tree.inputs if in_out == "INPUT" else node_tree.outputs
    if name not in sockets:
        sockets.new(socket_type, name)


def replace_input_link(node_tree, input_socket, output_socket):
    for link in list(input_socket.links):
        node_tree.links.remove(link)
    node_tree.links.new(output_socket, input_socket)


def get_socket(sockets, name, fallback_index=0):
    socket = sockets.get(name)
    if socket is not None:
        return socket
    return sockets[fallback_index]


def get_or_create_node(node_tree, node_type, name):
    node = node_tree.nodes.get(name)
    if node is not None and node.bl_idname == node_type:
        return node
    if node is not None:
        node_tree.nodes.remove(node)
    node = node_tree.nodes.new(node_type)
    node.name = name
    node.label = name
    return node


def new_node(node_tree, node_types):
    for node_type in node_types:
        try:
            return node_tree.nodes.new(node_type)
        except RuntimeError:
            continue
    raise RuntimeError("无法创建像素预览节点。")


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
    set_node_input_default(downscale_node, "X", -offset_x)
    set_node_input_default(downscale_node, "Y", -offset_y)
    set_node_input_default(upscale_node, "X", offset_x)
    set_node_input_default(upscale_node, "Y", offset_y)
    return True


def set_node_input_default(node, input_name, value):
    socket = node.inputs.get(input_name)
    if socket is not None and hasattr(socket, "default_value"):
        socket.default_value = value


def configure_transform_node(node):
    for property_name, value in (("filter_type", "NEAREST"), ("interpolation", "NEAREST"), ("extension", "CLIP")):
        if hasattr(node, property_name):
            try:
                setattr(node, property_name, value)
            except TypeError:
                pass


def ensure_viewport_pixel_group(preview_scale, offset_x=0.0, offset_y=0.0):
    group = bpy.data.node_groups.get(VIEWPORT_PIXEL_GROUP_NAME)
    if group is None or group.bl_idname != "CompositorNodeTree":
        group = bpy.data.node_groups.new(VIEWPORT_PIXEL_GROUP_NAME, "CompositorNodeTree")
    group.nodes.clear()
    ensure_group_socket(group, "Image", "INPUT")
    ensure_group_socket(group, "Image", "OUTPUT")
    input_node = group.nodes.new("NodeGroupInput")
    output_node = group.nodes.new("NodeGroupOutput")
    value_node = new_node(group, ("ShaderNodeValue", "CompositorNodeValue"))
    value_node.name = VIEWPORT_PIXEL_VALUE_NODE_NAME
    value_node.outputs[0].default_value = preview_scale
    downscale_node = group.nodes.new("CompositorNodeTransform")
    downscale_node.name = VIEWPORT_PIXEL_DOWNSCALE_NODE_NAME
    configure_transform_node(downscale_node)
    set_node_input_default(downscale_node, "X", -offset_x)
    set_node_input_default(downscale_node, "Y", -offset_y)
    gamma_node = new_node(group, ("ShaderNodeGamma", "CompositorNodeGamma"))
    gamma_node.label = "Neutral Spacer"
    divide_node = new_node(group, ("ShaderNodeMath", "CompositorNodeMath"))
    divide_node.operation = "DIVIDE"
    divide_node.inputs[0].default_value = 1.0
    upscale_node = group.nodes.new("CompositorNodeTransform")
    upscale_node.name = VIEWPORT_PIXEL_UPSCALE_NODE_NAME
    configure_transform_node(upscale_node)
    set_node_input_default(upscale_node, "X", offset_x)
    set_node_input_default(upscale_node, "Y", offset_y)
    replace_input_link(group, get_socket(downscale_node.inputs, "Image"), get_socket(input_node.outputs, "Image"))
    replace_input_link(group, get_socket(downscale_node.inputs, "Scale", 3), value_node.outputs[0])
    replace_input_link(group, get_socket(gamma_node.inputs, "Image"), get_socket(downscale_node.outputs, "Image"))
    replace_input_link(group, get_socket(upscale_node.inputs, "Image"), get_socket(gamma_node.outputs, "Image"))
    replace_input_link(group, divide_node.inputs[1], value_node.outputs[0])
    replace_input_link(group, get_socket(upscale_node.inputs, "Scale", 3), divide_node.outputs[0])
    replace_input_link(group, get_socket(output_node.inputs, "Image"), get_socket(upscale_node.outputs, "Image"))
    return group


def setup_viewport_pixel_preview(scene, preview_scale, offset_x=0.0, offset_y=0.0):
    node_tree = get_scene_compositor_tree(scene, create=True)
    if node_tree is None:
        raise RuntimeError("无法创建合成节点。")
    group = ensure_viewport_pixel_group(preview_scale, offset_x, offset_y)
    group_node = get_or_create_node(node_tree, "CompositorNodeGroup", VIEWPORT_PIXEL_GROUP_NODE_NAME)
    group_node.node_tree = group
    viewer_node = get_or_create_node(node_tree, "CompositorNodeViewer", VIEWPORT_PIXEL_VIEWER_NODE_NAME)
    render_layers_node = get_or_create_node(node_tree, "CompositorNodeRLayers", "SBK Render Layers")
    replace_input_link(node_tree, get_socket(group_node.inputs, "Image"), get_socket(render_layers_node.outputs, "Image"))
    replace_input_link(node_tree, get_socket(viewer_node.inputs, "Image"), get_socket(group_node.outputs, "Image"))
    connect_final_output(scene, node_tree, group_node)
    return group


def connect_final_output(scene, node_tree, group_node):
    if hasattr(scene, "compositing_node_group"):
        ensure_group_socket(node_tree, "Image", "OUTPUT")
        output_node = get_or_create_node(node_tree, "NodeGroupOutput", VIEWPORT_PIXEL_OUTPUT_NODE_NAME)
        replace_input_link(node_tree, get_socket(output_node.inputs, "Image"), get_socket(group_node.outputs, "Image"))
        return
    composite_node = get_or_create_node(node_tree, "CompositorNodeComposite", VIEWPORT_PIXEL_COMPOSITE_NODE_NAME)
    replace_input_link(node_tree, get_socket(composite_node.inputs, "Image"), get_socket(group_node.outputs, "Image"))


def remove_viewport_pixel_preview(scene):
    node_tree = get_scene_compositor_tree(scene)
    if node_tree is None:
        return 0
    removed = 0
    for name in (
        VIEWPORT_PIXEL_GROUP_NODE_NAME,
        VIEWPORT_PIXEL_VIEWER_NODE_NAME,
        VIEWPORT_PIXEL_COMPOSITE_NODE_NAME,
        VIEWPORT_PIXEL_OUTPUT_NODE_NAME,
    ):
        node = node_tree.nodes.get(name)
        if node is not None:
            node_tree.nodes.remove(node)
            removed += 1
    group = bpy.data.node_groups.get(VIEWPORT_PIXEL_GROUP_NAME)
    if group is not None and group.users == 0:
        bpy.data.node_groups.remove(group)
    return removed
