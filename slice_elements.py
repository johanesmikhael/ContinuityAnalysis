import ifcproducts
from ifcproducts import BuildingElement
from OCC.BRepAlgoAPI import BRepAlgoAPI_Section
from OCC.BRepAlgoAPI import BRepAlgoAPI_Common
from OCC.BRepBuilderAPI import BRepBuilderAPI_Copy
from OCC.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCC.TopTools import TopTools_ListIteratorOfListOfShape
from OCC.TopTools import TopTools_HSequenceOfShape
from OCC.TopTools import Handle_TopTools_HSequenceOfShape
from OCC.BRepAdaptor import BRepAdaptor_Curve
from OCC.TopExp import TopExp_Explorer
from OCC.TopAbs import *
from OCC.IntTools import IntTools_EdgeEdge
from OCC.AIS import AIS_Shape
import OCC.Quantity
import OCC.TopAbs
from OCC.Bnd import Bnd_Box
from OCC.BRepBndLib import brepbndlib_Add

from OCC.TopoDS import topods_Wire

from OCC.TopoDS import topods


class Slice(object):
    def __init__(self):
        self._element_slice_list = []
        #self.bottom_pt = None
        #self.upper_pt = None
        #self.left_pt = None
        #self.right_pt = None

    def add_element_slice(self, element_section):
        self._element_slice_list.append(element_section)

    def get_element_slice_list(self):
        return self._element_slice_list

    def clear_display(self, display):
        for element_slice in self._element_slice_list:
            element_slice.clear_display(display)

    def display_shape(self, display):
        for element_slice in self._element_slice_list:
            element_slice.display_shape(display)

    def display_coloured_shape(self, display, quantity_colour):
        for element_slice in self._element_slice_list:
            element_slice.display_coloured_shape(display, quantity_colour)

    def copy_slice(self, slice):
        for element_slice in slice.get_element_slice_list():
            element_slice_copy = element_slice.create_copy()
            self._element_slice_list.append(element_slice_copy)

    def set_visible(self, display, is_visibile):
        for element_slice in self._element_slice_list:
            if is_visibile:
                element_slice.show_shape(display)
            else:
                element_slice.hide_shape(display)

    '''def get_nearest_intersection_to_edges(self, edges):
        points = []
        for edge in edges:
            points.append(self.get_nearest_intersection(edge))
        return points

    def get_nearest_intersection(self, edge):
        nearest_param = None
        edge_curve = BRepAdaptor_Curve(edge)
        for element_section in self.get_element_section_list():
            param = element_section.nearest_intersection_element(edge)
            if param:
                if not nearest_param or nearest_param > param[0]:
                    nearest_param = param[0]
        if nearest_param:
            point = edge_curve.Value(nearest_param)
        else:
            last_param = edge_curve.LastParameter()
            point = edge_curve.Value(last_param)
        return point

    def get_nearest_intersection_element(self, edge):
        nearest_param = None
        edge_curve = BRepAdaptor_Curve(edge)
        for element_section in self._element_section_list:
            param = element_section.nearest_intersection_element(edge)
            if param:
                if not nearest_param or nearest_param[0] > param[0]:
                    nearest_param = param
        if nearest_param:
            point = edge_curve.Value(nearest_param[0])
            return point, nearest_param[1], nearest_param[2]
        else:
            return None'''


class ElementSlice(object):
    def __init__(self, *args):
        parent, element = args
        self.parent = parent
        self.element = element
        self.name = element.name
        self.is_decomposed = element.is_decomposed
        self.children = []
        self.shapes_slice = []
        #self.ais = []
        self.bounding_box = Bnd_Box()

    @staticmethod
    def create_element_slice(section_box, element, element_slice_parent=None):
        intersection = ElementSlice.check_intersection(section_box, element)
        if not intersection:
            return None
        element_slice = None
        if not element.is_decomposed:
            if len(element.topods_shapes) > 0:
                for shape in element.topods_shapes:
                    material = shape["material"]
                    topods_shape = ElementSlice.create_slice_from_shape(section_box, shape, element.bounding_box)
                    if topods_shape:  # indicating there is section between element and section plane
                        shape_slice = [topods_shape, material]
                        if not element_slice:
                            element_slice = ElementSlice(element_slice_parent, element)
                        element_slice.shapes_slice.append(shape_slice)
        else:  # element are composed by children elements
            children_element = element.children
            for child in children_element:
                child_slice = ElementSlice.create_element_slice(section_box, child, element_slice)
                if child_slice:
                    if not element_slice:
                        element_slice = ElementSlice(element_slice_parent, element)
                    child_slice.parent = element_slice
                    element_slice.children.append(child_slice)
        return element_slice

    @staticmethod
    def check_intersection(section_box, element):
        section_plane_b_box = section_box[4]
        element_b_box = element.bounding_box
        is_out = element_b_box.IsOut(section_plane_b_box)
        return not is_out

    @staticmethod
    def create_slice_from_shape(section_box, shape, bounding_box):
        slice_box_topods = section_box[1]
        topods_shape = []
        cut = BRepAlgoAPI_Common(slice_box_topods, shape["topods_shape"])
        shape = cut.Shape()
        test_bounding_box = Bnd_Box()
        brepbndlib_Add(shape, test_bounding_box)
        test_size = test_bounding_box.SquareExtent()
        if shape and test_size > 0:
            shape_dict = dict()
            shape_dict["topods_shape"] = shape
            topods_shape.append(shape_dict)
            '''# create explorer
            exp = OCC.TopExp.TopExp_Explorer(shape, OCC.TopAbs.TopAbs_FACE)
            while exp.More():
                face, surface_normal, orientation = BuildingElement.break_faces(exp.Current())
                exp.Next()
                face_dict = dict()
                face_dict["topods_shape"] = face
                topods_shape.append(face_dict)'''
            return topods_shape
        else:
            return None
        #print(shape)
        '''if not edge_list.IsEmpty():
            edges = TopTools_HSequenceOfShape()
            edges_handle = Handle_TopTools_HSequenceOfShape(edges)
            wires = TopTools_HSequenceOfShape()
            wires_handle = Handle_TopTools_HSequenceOfShape(wires)
            edge_list_iterator = TopTools_ListIteratorOfListOfShape(edge_list)
            while edge_list_iterator.More():
                edge = edge_list_iterator.Value()
                edge_list_iterator.Next()
                edges.Append(edge)
            ShapeAnalysis_FreeBounds.ConnectEdgesToWires(edges_handle, 1e-5, True, wires_handle)
            wires = wires_handle.GetObject()  #get TopTools_HSequenceOfShape from its handle
            for i in range(wires.Length()):
                wire_shape = wires.Value(i + 1)  # get TopoDS_Shape
                topods_wires.append(wire_shape)
            return topods_wires
        else:
            return None'''

    def display_shape(self, display):
        if not self.is_decomposed:
            ais_list = []
            for shape_slice in self.shapes_slice:
                material = shape_slice[1]
                ais_color = OCC.Quantity.Quantity_Color(0.1, 0.1, 0.1, OCC.Quantity.Quantity_TOC_RGB)
                transparency = 0
                if material is not None:
                    color = material.get_surface_colour()
                    ais_color = OCC.Quantity.Quantity_Color(color[0], color[1], color[2], OCC.Quantity.Quantity_TOC_RGB)
                    transparency = material.get_transparency()
                for shape in shape_slice[0]:
                    # ais = display.DisplayShape(shape, transparency=transparency)
                    ais_object = AIS_Shape(shape["topods_shape"])
                    ais_object.SetCurrentFacingModel(OCC.Aspect.Aspect_TOFM_BOTH_SIDE)
                    ais_object.SetColor(ais_color)
                    ais = ais_object.GetHandle()
                    display.Context.Display(ais)
                    display.Context.SetTransparency(ais, transparency)
                    # ais_list.append(ais)
                    shape["ais"] = ais
            #self.ais = ais_list
        else:
            for child in self.children:
                child.display_shape(display)

    def display_coloured_wire(self, display, quantity_colour):
        if not self.is_decomposed:
            ais_list = []
            for shape_section in self.shapes_section:
                material = shape_section[1]
                transparency = 0
                for shape in shape_section[0]:
                    # ais = display.DisplayShape(shape, transparency=transparency)
                    ais_object = AIS_Shape(shape)
                    ais = ais_object.GetHandle()
                    ais.GetObject().SetColor(quantity_colour)
                    display.Context.Display(ais)
                    display.Context.SetTransparency(ais, transparency)
                    ais_list.append(ais)
            self.ais = ais_list
        else:
            for child in self.children:
                child.display_coloured_wire(display, quantity_colour)

    def hide_shape(self, display):
        if not self.is_decomposed:
            for shape_slice in self.shapes_slice:
                for shape in shape_slice[0]:
                    display.Context.Erase(shape["ais"])
        else:
            for child in self.children:
                child.hide_shape(display)

    def show_shape(self, display):
        if not self.is_decomposed:
            for shape_slice in self.shapes_slice:
                for shape in shape_slice[0]:
                    display.Context.Display(shape["ais"])
        else:
            for child in self.children:
                child.show_shape(display)

    def clear_display(self, display):
        if not self.is_decomposed:
            for ais in self.ais:
                display.Context.Remove(ais)
        else:
            for child in self.children:
                child.clear_display(display)

    def create_copy(self):
        print("begin copy of %s" % self.name)
        element_slice = None
        if not self.is_decomposed:
            element_slice = ElementSlice(self.parent, self.element)
            for shape_slice in self.shapes_slice:
                topods_shapes, material = shape_slice
                topods_shapes_copy = []
                for topods_shape in topods_shapes:
                    shape_copy = BRepBuilderAPI_Copy(topods_shape["topods_shape"])
                    topods_shape_copy = shape_copy.Shape()
                    topods_shape_copy_dict = dict()
                    topods_shape_copy_dict["topods_shape"] = topods_shape_copy
                    topods_shapes_copy.append(topods_shape_copy_dict)
                    brepbndlib_Add(topods_shape_copy, element_slice.bounding_box)
                shape_slice_copy = [topods_shapes_copy, material]
                element_slice.shapes_slice.append(shape_slice_copy)
        else: #decomposed element
            element_slice = ElementSlice(self.parent, self.element)
            for child in self.children:
                child_copy = child.create_copy()
                element_slice.children.append(child_copy)
        return element_slice

    def update_bounding_box(self):
        self.bounding_box = Bnd_Box()
        if not self.is_decomposed:
            for shape_slice in self.shapes_slice:
                for topods_shape in shape_slice[0]:
                    brepbndlib_Add(topods_shape["topods_shape"], self.bounding_box)
                    x_min, y_min, z_min, x_max, y_max, z_max = self.bounding_box.Get()
                    x_minr = round(x_min, 4)
                    y_minr = round(y_min, 4)
                    z_minr = round(z_min, 4)
                    x_maxr = round(x_max, 4)
                    y_maxr = round(y_max, 4)
                    z_maxr = round(z_max, 4)
                    self.bounding_box.Update(x_minr, y_minr, z_minr, x_maxr, y_maxr, z_maxr )
        else:
            for child in self.children:
                child.update_bounding_box()
'''
    def nearest_intersection_element(self, edge):
        nearest_param = None
        if not self.is_decomposed:
            for shape_section in self.shapes_section:
                for shape in shape_section[0]:
                    exp = TopExp_Explorer(shape, TopAbs_EDGE)
                    while exp.More():
                        shape_edge = topods.Edge(exp.Current())
                        intersection = IntTools_EdgeEdge(edge, shape_edge)
                        intersection.Perform()
                        if intersection.IsDone():
                            commonparts = intersection.CommonParts()
                            for i in range(commonparts.Length()):
                                commonpart = commonparts.Value(i+1)
                                parameter = commonpart.VertexParameter1()
                                if parameter > 0.0:
                                    if not nearest_param or nearest_param[0] > parameter:
                                        nearest_param = parameter, self, shape_section
                        exp.Next()
        else:
            for child in self.children:
                param = child.nearest_intersection_element(edge)
                if param:
                    if not nearest_param or nearest_param[0] > param[0]:
                        nearest_param = param
        return nearest_param'''


