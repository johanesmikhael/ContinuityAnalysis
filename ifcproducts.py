from ifcopenshell.geom import occ_utils
import ifcopenshell

import OCC.TopExp
import OCC.TopAbs
import OCC.TopoDS
import OCC.BRep
import OCC.BRepTools
import OCC.GeomLProp
import OCC.Quantity
import OCC.Aspect
from ifcmaterials import *


class BuildingElement(object):
    def __init__(self, *args):
        parent, ifc_instance = args
        self.parent = parent
        self.ifcopenshell_setting = self.parent.ifcopenshell_setting
        self.ifc_instance = ifc_instance
        self.name = ifc_instance.Name
        self.guid = ifc_instance.GlobalId
        self.main_topods_shape = ifcopenshell.geom.create_shape(self.ifcopenshell_setting, ifc_instance).geometry
        self.element_display = None

    def display_shape(self, display):
        if self.main_topods_shape:
            print self.main_topods_shape
            self.element_display = display.DisplayShape(self.main_topods_shape)


class Slab(BuildingElement):
    def __init__(self, *args):
        super(Slab, self).__init__(*args)
        self.material_layers = []
        self.topods_faces = []
        self.get_material_properties()
        self.break_geometry()

    def get_material_properties(self):
        material_dict = self.parent.get_material_dict()
        associations = self.ifc_instance.HasAssociations
        material_association = None
        for association in associations:
            if association.is_a("IfcRelAssociatesMaterial"):
                material_association = association
                break
        relating_material = material_association.RelatingMaterial
        if relating_material.is_a("IfcMaterialLayerSetUsage"):
            material_layer_set = material_association.RelatingMaterial.ForLayerSet  # get IfcMaterialLayerSet
        else:
            return
        material_layers = material_layer_set.MaterialLayers
        for ifc_material_layer in material_layers:
            ifc_material = ifc_material_layer.Material
            material = material_dict.add_material(ifc_material)
            material_thickness = ifc_material_layer.LayerThickness
            material_layer = MaterialLayer(material, material_thickness)
            self.material_layers.append(material_layer)

    def break_geometry(self):
        # create explorer
        exp = OCC.TopExp.TopExp_Explorer(self.main_topods_shape, OCC.TopAbs.TopAbs_FACE)
        while exp.More():
            face = OCC.TopoDS.topods.Face(exp.Current())
            u_min, u_max, v_min, v_max = OCC.BRepTools.breptools_UVBounds(face)
            exp.Next()
            surface_handle = OCC.BRep.BRep_Tool.Surface(face)
            props = OCC.GeomLProp.GeomLProp_SLProps(surface_handle, (u_min + u_max) / 2, (v_min + v_max) / 2, 1, 0.01)
            surface_normal = props.Normal()
            orientation = face.Orientation()
            if orientation == OCC.TopAbs.TopAbs_REVERSED:
                surface_normal.Reverse()
            if surface_normal.Z() == -1:  # downward face
                material_layer = self.material_layers[len(self.material_layers) - 1]
            else:
                print len(self.material_layers)
                material_layer = self.material_layers[0]
            face_dict = dict()
            face_dict["topods_face"] = face
            face_dict["gp_dir_normal"] = surface_normal
            face_dict["material"] = material_layer.get_material()
            face_dict["ais"] = None
            self.topods_faces.append(face_dict)

    def display_shape(self, display):
        for shape in self.topods_faces:
            material = shape["material"]
            color = material.surface_colour
            ais_color = OCC.Quantity.Quantity_Color(color[0], color[1], color[2], OCC.Quantity.Quantity_TOC_RGB)
            ais = display.DisplayShape(shape["topods_face"], transparency=material.transparency).GetObject()
            ais.SetCurrentFacingModel(OCC.Aspect.Aspect_TOFM_BOTH_SIDE)
            ais.SetColor(ais_color)
            shape["ais"] = ais


class Wall(BuildingElement):
    def __init__(self, *args):
        super(Wall, self).__init__(*args)
        self.material_layers = []
        self.topods_faces = []


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
