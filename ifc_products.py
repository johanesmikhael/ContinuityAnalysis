from ifcopenshell.geom import occ_utils
import ifcopenshell


class BuildingElement(object):
    def __init__(self, *args):
        setting, ifc_instance = args
        self.ifcopenshell_setting = setting
        self.ifc_instance = ifc_instance
        self.name = ifc_instance.Name
        self.guid = ifc_instance.GlobalId
        self.occ_shape = ifcopenshell.geom.create_shape(self.ifcopenshell_setting, ifc_instance).geometry
        self.element_display = None

    def display_shape(self, display):
        if self.occ_shape:
            self.element_display = display.DisplayShape(self.occ_shape)


class Slab(BuildingElement):
    def __init__(self, *args):
        super(Slab, self).__init__(*args)
        self.material_layers = []


class Wall(BuildingElement):
    def __init__(self, *args):
        super(Wall, self).__init__(*args)


class Column(BuildingElement):
    def __init__(self, *args):
        super(Column, self).__init__(*args)


class Door(BuildingElement):
    def __init__(self, *args):
        super(Door, self).__init__(*args)


class Window(BuildingElement):
    def __init__(self, *args):
        super(Window, self).__init__(*args)


class Covering(BuildingElement):
    def __init__(self, *args):
        super(Covering, self).__init__(*args)


class Railing(BuildingElement):
    def __init__(self, *args):
        super(Railing, self).__init__(*args)


class Plate(BuildingElement):
    def __init__(self, *args):
        pass


class Material:
    def __init__(self):
        pass


class MaterialLayer:
    def __init__(self, material, thickness):
        self.material = material
        self.thickness = thickness
