import ifcproducts
from OCC.BRepAlgoAPI import BRepAlgoAPI_Section
from OCC.BRepBuilderAPI import BRepBuilderAPI_Copy
from OCC.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCC.TopTools import TopTools_ListIteratorOfListOfShape
from OCC.TopTools import TopTools_HSequenceOfShape
from OCC.TopTools import Handle_TopTools_HSequenceOfShape

import OCC.Quantity

from OCC.TopoDS import topods_Wire


class ElementSection(object):
    def __init__(self, *args):
        parent, element = args
        self.parent = parent
        self.element = element
        self.name = element.name
        self.is_decomposed = element.is_decomposed
        self.children = []
        self.shapes_section = []
        self.ais = []

    @staticmethod
    def create_element_section(section_plane, element, element_section_parent=None):
        element_section = None
        if not element.is_decomposed:
            if len(element.topods_shapes) > 0:
                for shape in element.topods_shapes:
                    material = shape["material"]
                    topods_wires = ElementSection.create_section_from_shape(section_plane, shape)
                    if topods_wires:  # indicating there is section between element and section plane
                        shape_section = [topods_wires, material]
                        if not element_section:
                            element_section = ElementSection(element_section_parent, element)
                        element_section.shapes_section.append(shape_section)
        else:  # element are composed by children elements
            children_element = element.children
            for child in children_element:
                child_section = ElementSection.create_element_section(section_plane, child, element_section)
                if child_section:
                    if not element_section:
                        element_section = ElementSection(element_section_parent, element)
                    child_section.parent = element_section
                    element_section.children.append(child_section)
        return element_section

    @staticmethod
    def create_section_from_shape(section_plane, shape):
        section_plane_face = section_plane[1]
        topods_wires = []
        section = BRepAlgoAPI_Section(section_plane_face, shape["topods_shape"])
        edge_list = section.SectionEdges()
        if not edge_list.IsEmpty():
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
            wires = wires_handle.GetObject()
            for i in range(wires.Length()):
                wire_shape = wires.Value(i + 1)
                topods_wire = topods_Wire(wire_shape)
                topods_wires.append(topods_wire)
            return topods_wires
        else:
            return None

    def display_wire(self, display):
        print "DISPLAY WIRE"
        if not self.is_decomposed:
            ais_list = []
            for shape_section in self.shapes_section:
                print shape_section
                material = shape_section[1]
                ais_color = OCC.Quantity.Quantity_Color(0.1, 0.1, 0.1, OCC.Quantity.Quantity_TOC_RGB)
                print material
                transparency = 0
                if material is not None:
                    color = material.get_shading_colour()
                    ais_color = OCC.Quantity.Quantity_Color(color[0], color[1], color[2], OCC.Quantity.Quantity_TOC_RGB)
                    transparency = material.get_transparency()
                for shape in shape_section[0]:
                    ais = display.DisplayShape(shape, transparency=transparency).GetObject()
                    ais.SetColor(ais_color)
                    ais_list.append(ais)
            self.ais = ais_list
        else:
            for child in self.children:
                child.display_wire(display)

    def clear_display(self, display):
        if not self.is_decomposed:
            for ais in self.ais:
                print ais
                display.Context.Remove(ais)
        else:
            for child in self.children:
                child.clear_display(display)

    def create_copy(self):
        element_section = None
        if not self.is_decomposed:
            element_section = ElementSection(self.parent, self.element)
            for shape_section in self.shapes_section:
                topods_wires, material = shape_section
                topods_wires_copy = []
                for topods_wire in topods_wires:
                    wire_copy = BRepBuilderAPI_Copy(topods_wire)
                    topods_wire_copy = wire_copy.Shape()
                    topods_wires_copy.append(topods_wire_copy)
                shape_section_copy = [topods_wires_copy, material]
                element_section.shapes_section.append(shape_section_copy)
        else: #decomposed element
            element_section = ElementSection(self.parent, self.element)
            for child in self.children:
                child_copy = child.create_copy()
                element_section.children.append(child_copy)
        return element_section



