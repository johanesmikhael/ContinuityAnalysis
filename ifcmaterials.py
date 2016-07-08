class Material(object):
    def __init__(self, ifc_material):
        self.ifc_material = ifc_material
        self.name = self.ifc_material.Name
        self.surface_colour = None
        self.transparency = None
        self.diffuse_colour = None
        self.reflectance_method = None
        has_representation = self.ifc_material.HasRepresentation
        if has_representation:
            material_definition_representation = has_representation[0]
            representation = material_definition_representation.Representations[0]
            representation_item = representation.Items[0]  # get IfcStyledItem
            style_assignement = representation_item.Styles[0]
            style_select = style_assignement.Styles[0]
            if style_select.is_a("IfcSurfaceStyle"):
                surface_style_element_select = style_select.Styles[0]
                if surface_style_element_select.is_a("IfcSurfaceStyleShading"):
                    self.surface_colour = Material.get_rgb_tuple(surface_style_element_select.SurfaceColour)
                    self.transparency = surface_style_element_select.Transparency
                    self.diffuse_colour = Material.get_rgb_tuple_or_factor(surface_style_element_select.DiffuseColour)
                    self.reflectance_method = surface_style_element_select.ReflectanceMethod

    @staticmethod
    def get_rgb_tuple(ifc_colour_rgb):
        rgb_tuple = (ifc_colour_rgb.Red, ifc_colour_rgb.Green, ifc_colour_rgb.Blue)
        return rgb_tuple

    @staticmethod
    def get_rgb_tuple_or_factor(ifc_colour_or_factor):
        if ifc_colour_or_factor is not None:
            if ifc_colour_or_factor.is_a("IfcColourRgb"):
                return Material.get_rgb_tuple(ifc_colour_or_factor)
            else:
                return ifc_colour_or_factor
        else:
            return None


class MaterialLayer(object):
    def __init__(self, *args):
        material, layer_thickness = args
        self.material = material
        self.thickness =  layer_thickness
    def get_material(self):
        return self.material


class MaterialDict(object):
    def __init__(self):
        self.material_dict = dict()

    def add_material(self, *args):
        ifc_material = args[0]
        material_name = ifc_material.Name
        if material_name in self.material_dict:  # material already exist
            print "material \"%s\" already exist in material list" %material_name
            material = self.material_dict[material_name]
            return material
        else:  # create materials
            print "material \"%s\" is not exist in material list" %material_name
            material = Material(ifc_material)
            self.material_dict[material_name] = material
            return material

    def get_material(self, *args):
        material_name = args[0]
        return self.material_dict.get(material_name, default=None)
