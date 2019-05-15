class Material(object):
    reflectance_methods = dict()
    reflectance_methods[0] = "blinn"  # smooth, slightly shiny appearance.
    reflectance_methods[1] = "flat"  # constant colour
    reflectance_methods[2] = "glass"  # glass-like materials
    reflectance_methods[3] = "matt"  # dull matte appearance
    reflectance_methods[4] = "metal"  # specular metallic appearanc
    reflectance_methods[5] = "mirror"  # secondary mirrored views through ray tracing
    reflectance_methods[6] = "phong"  # specular effect
    reflectance_methods[7] = "plastic"  # specular effect which is similar to the Phong model
    reflectance_methods[8] = "strauss" # metallic and non-metallic appearance based on a limited set of control parameter

    def __init__(self, ifc_material = None):
        self.ifc_material = ifc_material
        self.surface_style_name = None
        self.surface_colour = None
        self.transparency = None
        self.diffuse_colour = None
        self.reflection_colour = None
        self.reflectance = None #not ifc
        self.reflectance_method = None
        self.reflectance_method_enum = None
        self.slip_coefficient = None #not ifc
        self.imperviousness = None #not ifc
        if self.ifc_material:
            self.name = self.ifc_material.Name
            has_representation = self.ifc_material.HasRepresentation
            if has_representation:
                material_definition_representation = has_representation[0]
                representation = material_definition_representation.Representations[0]
                representation_item = representation.Items[0]  # get IfcStyledItem
                style_assignement = representation_item.Styles[0]
                style_select = style_assignement.Styles[0]
                if style_select.is_a("IfcSurfaceStyle"):
                    surface_style_element_select = style_select.Styles[0]
                    self.surface_style_name = style_select.Name
                    if surface_style_element_select.is_a("IfcSurfaceStyleShading"):
                        self.surface_colour = Material.get_rgb_tuple(surface_style_element_select.SurfaceColour)
                        self.transparency = surface_style_element_select.Transparency
                        self.diffuse_colour = Material.get_rgb_tuple_or_factor(surface_style_element_select.DiffuseColour)
                        self.reflection_colour = Material.get_rgb_tuple_or_factor(surface_style_element_select.ReflectionColour)
                        self.reflectance_method = surface_style_element_select.ReflectanceMethod
                        print("reflectance method {}".format(self.reflectance_method))
                        print("reflection colour {}".format(self.reflection_colour))
            else:
                self.surface_colour = (0.125, 0.125, 0.125)
                self.transparency = 0
        else:
            self.name = "default_material"

    def get_surface_colour(self):
        if self.surface_colour:
            return self.surface_colour
        else:
            return 0.125, 0.125, 0.125

    def set_surface_colour(self, r, g ,b):
        self.surface_colour = r, g , b

    def get_shading_colour(self):  # reduced colour scale to prevent overbright
        r, g, b = self.get_surface_colour()
        constant = 0.5
        return constant * r, constant * g, constant * b

    def get_transparency(self):
        if self.transparency:
            return self.transparency
        else:
            return 0.0

    def set_transparency(self, transparency):
        self.transparency = transparency

    def get_reflectance_method(self):
        if self.reflectance_method_enum:
            return self.reflectance_method_enum
        else:
            return 0

    def set_reflectance_method(self, reflectance_method_enum):
        self.reflectance_method_enum = reflectance_method_enum

    def get_reflectance(self):
        if self.reflectance:
            return self.reflectance
        else:
            return 0.0

    def set_reflectance(self, reflectance):
        self.reflectance = reflectance

    def get_slip_coefficient(self):
        if self.slip_coefficient:
            return self.slip_coefficient
        else:
            return 0.0

    def set_slip_coefficient(self, slip_coefficient):
        self.slip_coefficient = slip_coefficient

    def get_imperviousness(self):
        if self.imperviousness:
            return self.imperviousness
        else:
            return 0.0

    def set_imperviousness(self, imperviousness):
        self.imperviousness = imperviousness

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
        self.thickness = layer_thickness

    def get_material(self):
        return self.material


class MaterialDict(object):
    def __init__(self):
        self.material_dict = dict()
        self.material_dict_by_surface_style = dict()

    def add_default_material(self):
        return self.add_material()

    def add_material(self, ifc_material=None):
        if ifc_material:
            material_name = ifc_material.Name
        else:
            material_name = "default_material"
        if material_name in self.material_dict:  # material already exist
            print("material \"%s\" already exist in material list" % material_name)
            material = self.material_dict[material_name]
            return material
        else:  # create materials
            print("material \"%s\" is not exist in material list" % material_name)
            material = Material(ifc_material)
            print(material.get_surface_colour())
            self.material_dict[material_name] = material
            return material

    def add_material_by_style_select(self, style_select):
        material_name = style_select.Name
        if material_name in self.material_dict:
            print("material \"%s\" already exist in material list" % material_name)
            material = self.material_dict[material_name]
            return material
        else:
            print("material \"%s\" is not exist in material list" % material_name)
            material = Material()
            surface_style_element_select = style_select.Styles[0]
            surface_color = Material.get_rgb_tuple(surface_style_element_select.SurfaceColour)
            material.surface_colour = surface_color
            material.transparency = surface_style_element_select.Transparency
            material.diffuse_colour = Material.get_rgb_tuple_or_factor(surface_style_element_select.DiffuseColour)
            material.reflectance_method = surface_style_element_select.ReflectanceMethod
            print(material.get_surface_colour())
            self.material_dict[material_name] = material
            return material
        pass

    def add_material_by_style(self, material):
        self.material_dict_by_surface_style[material.surface_style_name] = material

    def get_material(self, *args):
        material_name = args[0]
        return self.material_dict.get(material_name)

    def get_default_material(self):
        return self.material_dict.get("default_material")

    def get_material_by_surface_style(self, *args):
        surface_style_name = args[0]
        return self.material_dict_by_surface_style.get(surface_style_name)

    def get_material_information(self, ifc_instance):
        associations = ifc_instance.HasAssociations
        material_association = None
        for association in associations:
            if association.is_a("IfcRelAssociatesMaterial"):
                material_association = association
                break
        if material_association is None:
            material = self.add_material()
            return "IfcMaterial", material
        relating_material = material_association.RelatingMaterial
        if relating_material.is_a("IfcMaterialLayerSetUsage"):
            material_layers = self.get_material_layers_from_set_usage(relating_material)
            return "IfcMaterialLayerSetUsage", material_layers
        elif relating_material.is_a("IfcMaterialLayerSet"):
            pass
        elif relating_material.is_a("IfcMaterialLayer"):
            pass
        elif relating_material.is_a("IfcMaterialList"):
            material_list = self.get_material_list(relating_material)
            return "IfcMaterialList", material_list
            pass
        elif relating_material.is_a("IfcMaterial"):
            material = self.add_material(relating_material)
            return "IfcMaterial", material
            pass
        else:
            material = self.add_material()
            return "IfcMaterial", material

    def get_material_list(self, relating_material):
        material_list = []
        for ifc_material in relating_material.Materials:
            print(ifc_material)
            material = self.add_material(ifc_material)
            material_list.append(material)
        return material_list

    def get_material_layers_from_set_usage(self, relating_material):
        material_layer_set = relating_material.ForLayerSet
        ifc_material_layers = material_layer_set.MaterialLayers
        material_layers = []
        for ifc_material_layer in ifc_material_layers:
            ifc_material = ifc_material_layer.Material
            material = self.add_material(ifc_material)
            material_thickness = ifc_material_layer.LayerThickness
            material_layer = MaterialLayer(material, material_thickness)
            material_layers.append(material_layer)
        return material_layers
