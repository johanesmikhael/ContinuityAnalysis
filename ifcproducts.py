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

import sys, inspect


class ElementSelect():
    def __init__(self):
        self.create_function_dict = dict()

    def add_function_to_dict(self, ifc_element_type_name, _callable):
        assert callable(_callable), "the function supplied is not callable"
        self.create_function_dict[ifc_element_type_name] = _callable

    def create(self, *args):
        parent, ifc_instance = args
        ifc_element_type_name = ifc_instance.is_a()
        _callable = self.create_function_dict[ifc_element_type_name]
        if _callable is None:
            print "Selected element type is not exist"
            return None
        else:
            element = _callable(parent, ifc_instance)
            return element


element_select = ElementSelect()


def create_slab(*args):
    slab = Slab(*args)
    return slab

element_select.add_function_to_dict("IfcSlab", create_slab)


def create_wall(*args):
    return Wall(*args)

element_select.add_function_to_dict("IfcWall", create_wall)


def create_standard_wall(*args):
    return Wall(*args)

element_select.add_function_to_dict("IfcWallStandardCase", create_standard_wall)


def create_column(*args):
    return Column(*args)

element_select.add_function_to_dict("IfcColumn", create_column)


def create_beam(*args):
    return Beam(*args)

element_select.add_function_to_dict("IfcBeam", create_beam)


def create_door(*args):
    return Door(*args)

element_select.add_function_to_dict("IfcDoor", create_door)


def create_window(*args):
    return Window(*args)

element_select.add_function_to_dict("IfcWindow", create_window)


def create_covering(*args):
    return Covering(*args)
element_select.add_function_to_dict("IfcCovering", create_covering)


def create_curtain_wall(*args):
    return CurtainWall(*args)
element_select.add_function_to_dict("IfcCurtainWall", create_curtain_wall)


def create_plate(*args):
    return Plate(*args)
element_select.add_function_to_dict("IfcPlate", create_plate)


def create_member(*args):
    return Member(*args)
element_select.add_function_to_dict("IfcMember", create_member)


def create_stair(*args):
    return Stair(*args)
element_select.add_function_to_dict("IfcStair", create_stair)


def create_stair_flight(*args):
    return StairFlight(*args)
element_select.add_function_to_dict("IfcStairFlight", create_stair_flight)


def create_railing(*args):
    return Railing(*args)
element_select.add_function_to_dict("IfcRailing", create_railing)


def create_roof(*args):
    return Roof(*args)
element_select.add_function_to_dict("IfcRoof", create_roof)


def create_furniture(*args):
    return Furniture(*args)
element_select.add_function_to_dict("IfcFurnishingElement", create_furniture)


def create_flow_terminal(*args):
    return FlowTerminal(*args)
element_select.add_function_to_dict("IfcFlowTerminal", create_flow_terminal)


def create_building_element_proxy(*args):
    return BuildingElementProxy(*args)
element_select.add_function_to_dict("IfcBuildingElementProxy", create_building_element_proxy)


class BuildingElement(object):
    def __init__(self, *args):
        parent, ifc_instance = args
        self.parent = parent
        self.ifcopenshell_setting = self.parent.ifcopenshell_setting
        self.ifc_instance = ifc_instance
        self.name = ifc_instance.Name
        self.guid = ifc_instance.GlobalId
        self.is_decomposed = BuildingElement.check_ifc_is_decomposed(self.ifc_instance)
        self.children = []
        self.main_topods_shape = self.get_topods_shape()
        self.topods_shapes = []
        self.main_ais = None
        self.material_dict = self.parent.get_material_dict()
        self.material_information = self.material_dict.get_material_information(self.ifc_instance)

    def get_topods_shape(self):
        if not self.is_decomposed:
            return ifcopenshell.geom.create_shape(self.ifcopenshell_setting, self.ifc_instance).geometry
        else:
            return None

    def display_shape(self, display):
        if len(self.children) > 0:
            self.display_children(display)
        if len(self.topods_shapes) > 0:
            self.display_from_topods_shapes(display)
        elif self.main_topods_shape:
            self.main_ais = display.DisplayShape(self.main_topods_shape)

    def display_children(self, display):
        for child in self.children:
            child.display_shape(display)

    def display_from_topods_shapes(self, display):
        for shape in self.topods_shapes:
            material = shape["material"]
            ais_color = OCC.Quantity.Quantity_Color(0.1, 0.1, 0.1, OCC.Quantity.Quantity_TOC_RGB)
            transparency = 0
            if material is not None:
                color = material.get_shading_colour()
                ais_color = OCC.Quantity.Quantity_Color(color[0], color[1], color[2], OCC.Quantity.Quantity_TOC_RGB)
                transparency = material.get_transparency()
            ais = display.DisplayShape(shape["topods_shape"], transparency=transparency).GetObject()
            ais.SetCurrentFacingModel(OCC.Aspect.Aspect_TOFM_BOTH_SIDE)
            ais.SetColor(ais_color)
            shape["ais"] = ais

    def get_material_layers(self):
        material_layers = []
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
        return material_layers

    def put_main_shape_to_shape_list(self):
        shape_dict = dict()
        shape_dict["topods_shape"] = self.main_topods_shape
        shape_dict["material"] = self.material_information[1]
        self.topods_shapes.append(shape_dict)

    def analyze_representation(self):
        if not self.is_decomposed:
            self.break_non_decomposed_geometry()
        else:
            self.break_decomposed_geometry()

    def break_non_decomposed_geometry(self):
        ifc_product_representation = self.ifc_instance.Representation
        ifc_representations = ifc_product_representation.Representations
        material_list = []
        for ifc_representation in ifc_representations:
            if ifc_representation.RepresentationIdentifier == "Body":
                if ifc_representation.RepresentationType == "MappedRepresentation":
                    for item in ifc_representation.Items:
                        mapped_representation = item.MappingSource.MappedRepresentation
                        mapped_representation_items = mapped_representation.Items
                        for mapped_representation_item in mapped_representation_items:
                            if not mapped_representation_item.is_a("IfcFaceBasedSurfaceModel"):
                                ifc_styled_item = mapped_representation_item.StyledByItem[0]  # get IfcStyledItem
                                style_assignment = ifc_styled_item.Styles[0]
                                style_select = style_assignment.Styles[0]
                                material = self.material_dict.get_material(style_select.Name)
                                material_list.append(material)
                            else:
                                fbsm_faces = mapped_representation_item.FbsmFaces
                                if mapped_representation_item.StyledByItem:
                                    ifc_styled_item = mapped_representation_item.StyledByItem[0]  # get IfcStyledItem
                                    style_assignment = ifc_styled_item.Styles[0]
                                    style_select = style_assignment.Styles[0]
                                    material = self.material_dict.get_material(style_select.Name)
                                    for fbsm_face in fbsm_faces:
                                        material_list.append(material)
                                else:
                                    for fbsm_face in fbsm_faces:
                                        material_list.append(None)
                else:
                    for item in ifc_representation.Items:
                        if not item.is_a("IfcBooleanClippingResult"):
                            ifc_styled_item = item.StyledByItem[0]  # get IfcStyledItem
                        else:
                            first_operand_item = item.FirstOperand
                            while first_operand_item.is_a("IfcBooleanClippingResult"):
                                first_operand_item = first_operand_item.FirstOperand
                            ifc_styled_item = first_operand_item.StyledByItem[0]
                        style_assignement = ifc_styled_item.Styles[0]
                        style_select = style_assignement.Styles[0]
                        material = self.material_dict.get_material(style_select.Name)
                        material_list.append(material)
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

    def break_decomposed_geometry(self):
        ifc_rel_decomposes = self.ifc_instance.IsDecomposedBy
        for ifc_rel_decompose in ifc_rel_decomposes:
            ifc_object_definitions = ifc_rel_decompose.RelatedObjects
            for ifc_object_definition in ifc_object_definitions:
                element = element_select.create(self.parent, ifc_object_definition)
                self.children.append(element)


    @staticmethod
    def break_faces(current_exp):
        face = OCC.TopoDS.topods.Face(current_exp)
        u_min, u_max, v_min, v_max = OCC.BRepTools.breptools_UVBounds(face)
        surface_handle = OCC.BRep.BRep_Tool.Surface(face)
        props = OCC.GeomLProp.GeomLProp_SLProps(surface_handle, u_min, v_min, 1, 0.01)
        surface_normal = props.Normal()
        orientation = face.Orientation()
        return face, surface_normal, orientation

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
        self.break_slab_geometry()

    def break_slab_geometry(self):
        material_layers = self.get_material_layers()
        # create explorer
        exp = OCC.TopExp.TopExp_Explorer(self.main_topods_shape, OCC.TopAbs.TopAbs_FACE)
        while exp.More():
            face, surface_normal, orientation = BuildingElement.break_faces(exp.Current())
            exp.Next()
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
            face_dict["topods_shape"] = face
            face_dict["gp_dir_normal"] = surface_normal
            face_dict["ais"] = None
            self.topods_shapes.append(face_dict)


class Wall(BuildingElement):
    def __init__(self, *args):
        super(Wall, self).__init__(*args)
        if self.ifc_instance.is_a() == "IfcWallStandardCase":
            self.is_standard_case = True
        else:
            self.is_standard_case = False
        self.representation_type = BuildingElement.get_representation_type(self.ifc_instance)
        self.ref_rotation = self.get_ref_rotation()
        self.break_wall_geometry()

    def get_ref_rotation(self):
        placement = self.ifc_instance.ObjectPlacement
        depth = 0
        dir_ratios_list = []
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

    def break_wall_geometry(self):
        material_layers = self.get_material_layers()
        # create explorer
        exp = OCC.TopExp.TopExp_Explorer(self.main_topods_shape, OCC.TopAbs.TopAbs_FACE)
        while exp.More():
            face, surface_normal, orientation = BuildingElement.break_faces(exp.Current())
            exp.Next()
            face_dict = dict()
            if orientation == OCC.TopAbs.TopAbs_REVERSED:
                surface_normal.Reverse()
            if self.ref_rotation != 0.0:
                rotation_axis = OCC.gp.gp_Ax1()
                surface_normal.Rotate(rotation_axis,
                                      -self.ref_rotation)  # minus means rotate back to default coordinate
            if len(material_layers) > 0:
                if surface_normal.Y() == -1:  # facing backward
                    material_layer = material_layers[len(material_layers) - 1]
                else:
                    material_layer = material_layers[0]
                face_dict["material"] = material_layer.get_material()
            else:
                face_dict["material"] = None
            face_dict["topods_shape"] = face
            face_dict["gp_dir_normal"] = surface_normal
            face_dict["ais"] = None
            self.topods_shapes.append(face_dict)


class Column(BuildingElement):
    def __init__(self, *args):
        super(Column, self).__init__(*args)
        self.put_main_shape_to_shape_list()


class Beam(BuildingElement):
    def __init__(self, *args):
        super(Beam, self).__init__(*args)
        self.put_main_shape_to_shape_list()


class Door(BuildingElement):
    def __init__(self, *args):
        super(Door, self).__init__(*args)
        self.analyze_representation()


class Window(BuildingElement):
    def __init__(self, *args):
        super(Window, self).__init__(*args)
        self.topods_shapes = []
        self.children = []
        self.analyze_representation()


class Covering(BuildingElement):
    def __init__(self, *args):
        super(Covering, self).__init__(*args)
        self.covering_type = self.ifc_instance.PredefinedType
        self.break_covering_geometry()

    def break_covering_geometry(self):
        material_layers = self.get_material_layers()
        # create explorer
        exp = OCC.TopExp.TopExp_Explorer(self.main_topods_shape, OCC.TopAbs.TopAbs_FACE)
        while exp.More():
            face, surface_normal, orientation = self.break_faces(exp.Current())
            exp.Next()
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
            face_dict["topods_shape"] = face
            face_dict["gp_dir_normal"] = surface_normal
            face_dict["ais"] = None
            self.topods_shapes.append(face_dict)


class CurtainWall(BuildingElement):
    def __init__(self, *args):
        super(CurtainWall, self).__init__(*args)
        self.analyze_representation()


class Plate(BuildingElement):
    def __init__(self, *args):
        super(Plate, self).__init__(*args)
        self.analyze_representation()


class Member(BuildingElement):
    def __init__(self, *args):
        super(Member, self).__init__(*args)
        self.analyze_representation()


class Stair(BuildingElement):
    def __init__(self, *args):
        super(Stair, self).__init__(*args)
        self.analyze_representation()


class Railing(BuildingElement):
    def __init__(self, *args):
        super(Railing, self).__init__(*args)
        self.analyze_representation()


class StairFlight(BuildingElement):
    def __init__(self, *args):
        super(StairFlight, self).__init__(*args)
        self.analyze_representation()


class Roof(BuildingElement):
    def __init__(self, *args):
        super(Roof, self).__init__(*args)
        self.analyze_representation()


class Furniture(BuildingElement):
    def __init__(self, *args):
        super(Furniture, self).__init__(*args)
        self.analyze_representation()


class FlowTerminal(BuildingElement):
    def __init__(self, *args):
        super(FlowTerminal, self).__init__(*args)
        self.ifc_flow_terminal_type = self.get_flow_terminal_type()
        self.analyze_representation()

    def get_flow_terminal_type(self):
        ifc_rel_defines = self.ifc_instance.IsDefinedBy
        for ifc_rel_define in ifc_rel_defines:
            if ifc_rel_define.is_a("IfcRelDefinesByType"):
                flow_terminal_type = ifc_rel_define.RelatingType
                return flow_terminal_type.is_a(), flow_terminal_type.Name
                break
        return None


class BuildingElementProxy(BuildingElement):
    def __init__(self, *args):
        super(BuildingElementProxy, self).__init__(*args)
        self.ifc_building_element_proxy_type = self.get_building_element_proxy_type()
        self.analyze_representation()

    def get_building_element_proxy_type(self):
        ifc_rel_defines = self.ifc_instance.IsDefinedBy
        for ifc_rel_define in ifc_rel_defines:
            if ifc_rel_define.is_a("IfcRelDefinesByType"):
                flow_terminal_type = ifc_rel_define.RelatingType
                if flow_terminal_type:
                    return flow_terminal_type.is_a, flow_terminal_type.Name
                break
        return None


class Site(BuildingElement):
    def __init__(self, *args):
        super(Site, self).__init__(*args)
        if self.ifc_instance.Representation:
            self.main_topods_shape =  ifcopenshell.geom.create_shape(self.ifcopenshell_setting, self.ifc_instance).geometry
            representation = self.ifc_instance.Representation
            material_list = []
            for ifc_representation in representation.Representations:
                if ifc_representation.RepresentationIdentifier == "Body":
                    representation_items = ifc_representation.Items
                    print representation_items
                    for representation_item in representation_items:
                        fsbm_faces = representation_item.FbsmFaces
                        if representation_item.StyledByItem:
                            ifc_styled_item = representation_item.StyledByItem[0]
                            style_assignment = ifc_styled_item.Styles[0]
                            style_select = style_assignment.Styles[0]
                            material = self.material_dict.get_material(style_select.Name)
                            if material is None:
                                material = self.material_dict.add_material_by_style_select(style_select)
                            for fsbm_face in fsbm_faces:
                                material_list.append(material)
                        else:
                            for fsbm_face in fsbm_faces:
                                material_list.append(None)
            shape_iterator = OCC.TopoDS.TopoDS_Iterator(self.main_topods_shape)
            print len(material_list)
            j = 0
            while shape_iterator.More():
                topods_shape = shape_iterator.Value()
                shape_dict = dict()
                if j < len(material_list):
                    shape_dict["material"] = material_list[j]
                else:
                    shape_dict["material"] = None
                shape_dict["topods_shape"] = topods_shape
                self.topods_shapes.append(shape_dict)
                j += 1
                shape_iterator.Next()
