from . import materials, operators, properties, ui


CLASSES = (
    *properties.CLASSES,
    *operators.CLASSES,
    *ui.CLASSES,
)


def register_properties():
    properties.register_properties()
    materials.register_handlers()


def unregister_properties():
    materials.unregister_handlers()
    properties.unregister_properties()
