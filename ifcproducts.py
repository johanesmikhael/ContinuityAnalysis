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
import OCC.gp
from ifcmaterials import *


class BuildingElement(object):
    def __init__(self, *args):
        parent, ifc_instance = args
        self.parent = parent
        self.ifcopenshell_setting = self.parent.ifcopenshell_setting
        self.ifc_instance = ifc_instance
        self.name = ifc_instance.Name
        self.guid = ifc_instance.GlobalId
        self.is_decomposed = BuildingElement.check_ifc_is_decomposed(self.ifc_instance)
        self.main_topods_shape = self.get_topods_shape()
        self.main_ais = None
        self.material_dict = self.parent.get_material_dict()
        self.material_information = self.material_dict.get_material_information(self.ifc_instance)

    def get_topods_shape(self):
        if not self.is_decomposed:
            return ifcopenshell.geom.create_shape(self.ifcopenshell_setting, self.ifc_instance).geometry
        else:
            return None

    def display_shape(self, display):
        if self.main_topods_shape:
            self.main_ais = display.DisplayShape(self.main_topods_shape)

    @staticmethod
    def get_representation_type(*args):
        ifc_instance = args[0]
        product_representation = ifc_instance.Representation
        if product_representation:
            representations = product_representation.Representations
            for ifc_representation in representations:
                if ifc_representation.RepresentationIdentifier == "Body":
                    return ifc_representation.RepresentationType
        else:
            return None

    @staticmethod
    def check_ifc_is_decompose(ifc_instance):
        """print "########################START CHECK#########################"
        print ifc_instance
        print "Product name :"
        print ifc_instance.Name
        print "Is decomposed by"
        print ifc_instance.IsDecomposedBy
        print "Decomposes :"
        print ifc_instance.Decomposes
        print "##########################END CHECK#########################"''"""
        if ifc_instance.Decomposes:
            return True
        else:
            return False

    @staticmethod
    def check_ifc_is_decomposed(ifc_instance):
        if ifc_instance.IsDecomposedBy:
            return True
        else:
            return False


class Slab(BuildingElement):
    def __init__(self, *args):
        super(Slab, self).__init__(*args)
        self.topods_faces = []
        self.break_slab_geometry()

    def break_slab_geometry(self):
        if self.material_information:
            if self.material_information[0] == "IfcMaterialLayerSetUsage" or \
                            self.material_information[0] == "IfcMaterialLayerSet":
                material_layers = self.material_information[1]
            elif self.material_information[0] == "IfcMaterial":
                thickness = None  # temporarily, should not be None
                material_layer = MaterialLayer(self.material_information[1], thickness)
                material_layers = [material_layer]  # create new layer material if single material
        else:
            material_layers = []
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
            face_dict = dict()  # "topods_face", "material", "gp_dir_normal", "ais"
            if orientation == OCC.TopAbs.TopAbs_REVERSED:
                surface_normal.Reverse()
            if len(material_layers) > 0:
                if surface_normal.Z() == -1:  # downward face
                    material_layer = material_layers[len(material_layers) - 1]
                else:
                    material_layer = material_layers[0]
                face_dict["material"] = material_layer.get_material()
            else:
                face_dict["material"] = None
            face_dict["topods_face"] = face
            face_dict["gp_dir_normal"] = surface_normal
            face_dict["ais"] = None
            self.topods_faces.append(face_dict)

    def display_shape(self, display):
        for shape in self.topods_faces:
            material = shape["material"]
            ais_color = OCC.Quantity.Quantity_Color(0.1, 0.1, 0.1, OCC.Quantity.Quantity_TOC_RGB)
            transparency = 0
            if material is not None:
                color = material.get_shading_colour()
                ais_color = OCC.Quantity.Quantity_Color(color[0], color[1], color[2], OCC.Quantity.Quantity_TOC_RGB)
                transparency = material.get_transparency()
            ais = display.DisplayShape(shape["topods_face"], transparency=transparency).GetObject()
            ais.SetCurrentFacingModel(OCC.Aspect.Aspect_TOFM_BOTH_SIDE)
            ais.SetColor(ais_color)
            shape["ais"] = ais


class Wall(BuildingElement):
    def __init__(self, *args):
        super(Wall, self).__init__(*args)
        self.topods_faces = []
        if self.ifc_instance.is_a() == "IfcWallStandardCase":
            self.is_standard_case = True
        else:
            self.is_standard_case = False
        self.representation_type = BuildingElement.get_representation_type(self.ifc_instance)
        self.ref_rotation = self.get_ref_rotation()
        print "-----------------------------------------------------"
        print self.name
        print "is standard case: %s" % self.is_standard_case
        print "representation type: %s" % self.representation_type
        print "angle to default ref: %s" % self.ref_rotation
        self.break_ifc_standard_wall_geometry()

    def get_ref_rotation(self):
        placement = self.ifc_instance.ObjectPlacement
        depth = 0
        dir_ratios_list = []
        ref_direction = None
        while placement is not None:
            rel_placement = placement.RelativePlacement
            ref_direction = rel_placement.RefDirection
            if not ref_direction:
                dir_ratios = (1.0, 0.0, 0.0)
            else:
                dir_ratios = ref_direction.DirectionRatios
            dir_ratios_list.append(dir_ratios)
            placement = placement.PlacementRelTo
            depth += 1
        rotation = Wall.calculate_rotation_to_default_axis(dir_ratios_list)
        return rotation

    @staticmethod
    def calculate_rotation_to_default_axis(*args):
        dir_ratios_list = args[0]
        normal_ref = OCC.gp.gp_Dir(0, 0, 1)
        init_ref = OCC.gp.gp_Dir()
        rotation_angle = 0.0
        for dir_ratios in dir_ratios_list:
            x, y, z = dir_ratios
            ref_coordinate = OCC.gp.gp_XYZ(x, y, z)
            referenced_ref = OCC.gp.gp_Dir(ref_coordinate)
            angle = init_ref.AngleWithRef(referenced_ref, normal_ref)
            rotation_angle += angle
        return rotation_angle

    def break_ifc_standard_wall_geometry(self):
        if not self.is_standard_case:
            pass
        if self.material_information:
            if self.material_information[0] == "IfcMaterialLayerSetUsage" or \
                            self.material_information[0] == "IfcMaterialLayerSet":
                material_layers = self.material_information[1]
            elif self.material_information[0] == "IfcMaterial":
                thickness = None  # temporarily, should not be None
                material_layer = MaterialLayer(self.material_information[1], thickness)
                material_layers = [material_layer]  # create new layer material if single material
        else:
            material_layers = []
        # create explorer
        exp = OCC.TopExp.TopExp_Explorer(self.main_topods_shape, OCC.TopAbs.TopAbs_FACE)
        while exp.More():
            face = OCC.TopoDS.topods.Face(exp.Current())
            u_min, u_max, v_min, v_max = OCC.BRepTools.breptools_UVBounds(face)
            exp.Next()
            surface_handle = OCC.BRep.BRep_Tool.Surface(face)
            props = OCC.GeomLProp.GeomLProp_SLProps(surface_handle, u_min, v_min, 1, 0.01)
            surface_normal = props.Normal()
            orientation = face.Orientation()
            face_dict = dict()
            if orientation == OCC.TopAbs.TopAbs_REVERSED:
                surface_normal.Reverse()
            if self.ref_rotation != 0.0:
                rotation_axis = OCC.gp.gp_Ax1()
                surface_normal.Rotate(rotation_axis,
                                      -self.ref_rotation)  # minus means rotate back to default coordinate
            if len(material_layers) > 0:
                if surface_normal.Y() == -1:  # facing backward
                    print len(material_layers)
                    material_layer = material_layers[len(material_layers) - 1]
                else:
                    material_layer = material_layers[0]
                face_dict["material"] = material_layer.get_material()
            else:
                face_dict["material"] = None
            face_dict["topods_face"] = face
            face_dict["gp_dir_normal"] = surface_normal
            face_dict["ais"] = None
            self.topods_faces.append(face_dict)

    def display_shape(self, display):
        for shape in self.topods_faces:
            material = shape["material"]
            ais_color = OCC.Quantity.Quantity_Color(0.1, 0.1, 0.1, OCC.Quantity.Quantity_TOC_RGB)
            transparency = 0
            if material is not None:
                color = material.get_shading_colour()
                ais_color = OCC.Quantity.Quantity_Color(color[0], color[1], color[2], OCC.Quantity.Quantity_TOC_RGB)
                transparency = material.get_transparency()
            ais = display.DisplayShape(shape["topods_face"], transparency=transparency).GetObject()
            ais.SetCurrentFacingModel(OCC.Aspect.Aspect_TOFM_BOTH_SIDE)
            ais.SetColor(ais_color)
            shape["ais"] = ais


class Column(BuildingElement):
    def __init__(self, *args):
        super(Column, self).__init__(*args)
        print self.ifc_instance.Name
        print BuildingElement.get_representation_type(self.ifc_instance)

    def display_shape(self, display):
        material = self.material_information[1]
        ais_color = OCC.Quantity.Quantity_Color(0.1, 0.1, 0.1, OCC.Quantity.Quantity_TOC_RGB)
        transparency = 0
        if material is not None:
            color = material.get_shading_colour()
            ais_color = OCC.Quantity.Quantity_Color(color[0], color[1], color[2], OCC.Quantity.Quantity_TOC_RGB)
            transparency = material.get_transparency()
        self.main_ais = display.DisplayShape(self.main_topods_shape, transparency=transparency).GetObject()
        self.main_ais.SetCurrentFacingModel(OCC.Aspect.Aspect_TOFM_BOTH_SIDE)
        self.main_ais.SetColor(ais_color)


class Door(BuildingElement):
    def __init__(self, *args):
        super(Door, self).__init__(*args)
        self.topods_shapes = []
        self.analyze()

    def analyze(self):
        ifc_product_representation = self.ifc_instance.Representation
        ifc_representations = ifc_product_representation.Representations
        material_list = []
        for ifc_representation in ifc_representations:
            print ifc_representation
            if ifc_representation.RepresentationType == "MappedRepresentation":
                for item in ifc_representation.Items:
                    print item.MappingSource
                    print item.MappingTarget
                    print item.MappingSource.MappedRepresentation
                    print item.MappingSource.MappedRepresentation.Items
                    mapped_representation = item.MappingSource.MappedRepresentation
                    mapped_representation_items = mapped_representation.Items
                    i = 0
                    for mapped_representation_item in mapped_representation_items:
                        print"START ITEM %d" % i
                        ifc_styled_item = mapped_representation_item.StyledByItem[0] # get IfcStyledItem
                        print ifc_styled_item
                        style_assignement = ifc_styled_item.Styles[0]
                        print style_assignement
                        style_select = style_assignement.Styles[0]
                        print style_select
                        material = self.material_dict.get_material(style_select.Name)
                        print material.name
                        material_list.append(material)
                        i += 1
        shape_iterator = OCC.TopoDS.TopoDS_Iterator(self.main_topods_shape)
        j = 0
        while shape_iterator.More():
            topods_shape = shape_iterator.Value()
            shape_dict = dict()
            shape_dict["material"] = material_list[j]
            shape_dict["topods_shape"] = topods_shape
            self.topods_shapes.append(shape_dict)
            j += 1
            shape_iterator.Next()

    def display_shape(self, display):
        for topods_shape_dict in self.topods_shapes:
            material = topods_shape_dict["material"]
            topods_shape = topods_shape_dict["topods_shape"]
            ais_color = OCC.Quantity.Quantity_Color(0.1, 0.1, 0.1, OCC.Quantity.Quantity_TOC_RGB)
            transparency = 0
            if material is not None:
                color = material.get_shading_colour()
                ais_color = OCC.Quantity.Quantity_Color(color[0], color[1], color[2], OCC.Quantity.Quantity_TOC_RGB)
                transparency = material.get_transparency()
            topods_shape_ais = display.DisplayShape(topods_shape, transparency=transparency).GetObject()
            topods_shape_ais.SetCurrentFacingModel(OCC.Aspect.Aspect_TOFM_BOTH_SIDE)
            topods_shape_ais.SetColor(ais_color)
            topods_shape_dict["ais"] = topods_shape_ais
        pass


class Window(BuildingElement):
    def __init__(self, *args):
        super(Window, self).__init__(*args)


class Covering(BuildingElement):
    def __init__(self, *args):
        super(Covering, self).__init__(*args)
        self.covering_type = self.ifc_instance.PredefinedType
        self.topods_faces = []
        self.break_covering_geometry()

    def break_covering_geometry(self):
        if self.material_information:
            if self.material_information[0] == "IfcMaterialLayerSetUsage" or \
                            self.material_information[0] == "IfcMaterialLayerSet":
                material_layers = self.material_information[1]
            elif self.material_information[0] == "IfcMaterial":
                thickness = None  # temporarily, should not be None
                material_layer = MaterialLayer(self.material_information[1], thickness)
                material_layers = [material_layer]  # create new layer material if single material
        else:
            material_layers = []
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
            face_dict = dict()  # "topods_face", "material", "gp_dir_normal", "ais"
            if orientation == OCC.TopAbs.TopAbs_REVERSED:
                surface_normal.Reverse()
            if len(material_layers) > 0:
                if surface_normal.Z() == 1:
                    material_layer = material_layers[0]
                elif surface_normal.Z() == -1:
                    material_layer = material_layers[len(material_layers) - 1]
                else:  # non horizontal face
                    if self.covering_type == "CEILING":
                        material_layer = material_layers[len(material_layers) - 1]
                    else:
                        material_layer = material_layers[0]
                face_dict["material"] = material_layer.get_material()
            else:
                face_dict["material"] = None
            face_dict["topods_face"] = face
            face_dict["gp_dir_normal"] = surface_normal
            face_dict["ais"] = None
            self.topods_faces.append(face_dict)

    def display_shape(self, display):
        for shape in self.topods_faces:
            material = shape["material"]
            ais_color = OCC.Quantity.Quantity_Color(0.1, 0.1, 0.1, OCC.Quantity.Quantity_TOC_RGB)
            transparency = 0
            if material is not None:
                color = material.get_shading_colour()
                ais_color = OCC.Quantity.Quantity_Color(color[0], color[1], color[2], OCC.Quantity.Quantity_TOC_RGB)
                transparency = material.get_transparency()
            ais = display.DisplayShape(shape["topods_face"], transparency=transparency).GetObject()
            ais.SetCurrentFacingModel(OCC.Aspect.Aspect_TOFM_BOTH_SIDE)
            ais.SetColor(ais_color)
            shape["ais"] = ais


class Railing(BuildingElement):
    def __init__(self, *args):
        super(Railing, self).__init__(*args)


class CurtainWall(BuildingElement):
    def __init__(self, *args):
        super(CurtainWall, self).__init__(*args)


class Plate(BuildingElement):
    def __init__(self, *args):
        pass


class Roof(BuildingElement):
    def __init__(self, *args):
        pass


