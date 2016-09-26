from visualization import Ui_section_visualization
from PyQt4 import QtGui, QtCore
from section_visualization_widget import *

from OCC.gp import gp_Pnt, gp_Trsf, gp_Dir, gp_Ax1
from OCC.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_MakeEdge
from OCC.Graphic3d import  Graphic3d_EF_SVG

from OCC.TopExp import TopExp_Explorer
from OCC.TopAbs import *
from OCC.IntTools import IntTools_EdgeEdge

from OCC.TopoDS import topods
from OCC.BRepAdaptor import BRepAdaptor_Curve

from geom import points_to_bspline_curve

from section_elements import *

from analysis import *


class SectionAnalyzer(object):
    def __init__(self):
        self.section_list = []
        self._visualizer = None
        self.section_axis = None
        self.path_elevation = None
        self.domain_length = None
        self.section_distance = None
        self.section_planes = None
        self.dimension_analysis = None

    def add_section(self, section):
        self.section_list.append(section)

    def init(self, visualizer):
        self._visualizer = visualizer
        self.path_elevation = visualizer.parent.path_elevation
        self.domain_length = visualizer.parent.section_plane_size
        self.section_distance = visualizer.parent.section_distance
        self.section_planes = visualizer.parent.section_planes
        self.get_section()
        self.transform_section()
        self.display_section()
        self.display_axis()

    def get_section(self):
        for section in self._visualizer.parent.section_list:
            section_copy = Section()
            section_copy.copy_section(section)
            self.section_list.append(section_copy)

    def transform_section(self):
        distance = self.section_distance
        section_planes = self.section_planes
        i = 0
        for section in self.section_list:
            section_plane = section_planes[i]
            section_plane_pln = section_plane[3]
            translation = self.get_translation(section_plane_pln, i, distance)
            rotation = self.get_rotation(section_plane_pln, i, distance)
            for element in section.get_element_section_list():
                self.transform_element(element, translation)
                self.transform_element(element, rotation)
            i += 1

    def display_section(self):
        display = self._visualizer.canvas.get_display()
        for section in self.section_list:
            section.display_wire(display)

    def display_axis(self):
        gp_pnt_0 = gp_Pnt(0.0, 0.0, self.path_elevation)
        n = len(self.section_list)
        gp_pnt_1 = gp_Pnt(n*self._visualizer.parent.section_distance, 0.0, self.path_elevation)
        points = [gp_pnt_0, gp_pnt_1]
        crv = points_to_bspline_curve(points, 1)
        ais = self._visualizer.canvas.get_display().DisplayShape(crv)
        self.section_axis = [crv, ais]

    @staticmethod
    def get_translation(section_plane_pln, n_section, section_distance):
        gp_axis_0 = section_plane_pln.Axis()
        gp_point_0 = gp_axis_0.Location()
        gp_point_1 = gp_Pnt(n_section * section_distance, 0.0, 1.0)
        gp_trsf = gp_Trsf()
        gp_trsf.SetTranslation(gp_point_0, gp_point_1)
        return gp_trsf

    @staticmethod
    def get_rotation(section_plane_pln, n_section, section_distance):
        gp_axis_0 = section_plane_pln.Axis()
        gp_point_1 = gp_Pnt(n_section * section_distance, 0.0, 1.0)
        gp_dir = gp_Dir()
        gp_axis_1 = gp_Ax1(gp_point_1, gp_dir)
        rotation_angle = gp_axis_0.Angle(gp_axis_1)
        print rotation_angle
        rotation_axis = gp_Ax1()
        rotation_axis.SetLocation(gp_point_1)
        gp_trsf = gp_Trsf()
        gp_dir_0 = gp_axis_0.Direction()
        if gp_dir_0.Y() >= 0: #the set the rotation direction by determine the axis direction in quadran
            gp_trsf.SetRotation(rotation_axis, -rotation_angle)
        else:
            gp_trsf.SetRotation(rotation_axis, rotation_angle)
        return gp_trsf


    @staticmethod
    def transform_element(element, gp_trsf):
        if not element.is_decomposed:
            for shape_section in element.shapes_section:
                new_topods_wires = []
                for topods_wire in shape_section[0]:
                    new_topods_wires.append(BRepBuilderAPI_Transform(topods_wire, gp_trsf).Shape())
                shape_section[0] = new_topods_wires
        else:
            for child in element.children:
                SectionAnalyzer.transform_element(child, gp_trsf)
        pass

    def analyze_dimension(self):
        self.dimension_analysis = DimensionAnalysis(self)
        self.dimension_analysis.perform()
        display = self._visualizer.canvas.get_display()
        self.dimension_analysis.display_dimension_edges(display)
        '''for i, section in enumerate(self.section_list):
            x = i * self._visualizer.parent.section_distance
            origin_point = gp_Pnt(x, 0.0, self.path_elevation)
            bottom_point = gp_Pnt(x, 0.0, self.path_elevation-self.domain_length)
            upper_point = gp_Pnt(x, 0.0, self.path_elevation+self.domain_length)
            left_point = gp_Pnt(x, -self.domain_length, self.path_elevation)
            right_point = gp_Pnt(x, self.domain_length, self.path_elevation)
            bottom_section_edge = BRepBuilderAPI_MakeEdge(origin_point, bottom_point).Edge()
            upper_section_edge = BRepBuilderAPI_MakeEdge(origin_point, upper_point).Edge()
            left_section_edge = BRepBuilderAPI_MakeEdge(origin_point, left_point).Edge()
            right_section_edge = BRepBuilderAPI_MakeEdge(origin_point, right_point).Edge()
            section.bottom_pt = self.get_nearest_intersection(bottom_section_edge, section)
            section.upper_pt = self.get_nearest_intersection(upper_section_edge, section)
            section.left_pt = self.get_nearest_intersection(left_section_edge, section)
            section.right_pt = self.get_nearest_intersection(right_section_edge, section)
            ais__yellow_color = OCC.Quantity.Quantity_Color(0, 0, 1, OCC.Quantity.Quantity_TOC_RGB)
            if section.bottom_pt:
                bottom_edge = BRepBuilderAPI_MakeEdge(origin_point, section.bottom_pt).Edge()
                ais = display.DisplayShape(bottom_edge).GetObject()
                ais.SetColor(ais__yellow_color)
            if section.upper_pt:
                upper_edge = BRepBuilderAPI_MakeEdge(origin_point, section.upper_pt).Edge()
                ais = display.DisplayShape(upper_edge).GetObject()
                ais.SetColor(ais__yellow_color)
            if section.left_pt:
                left_edge = BRepBuilderAPI_MakeEdge(origin_point, section.left_pt).Edge()
                ais = display.DisplayShape(left_edge).GetObject()
            if section.right_pt:
                right_edge = BRepBuilderAPI_MakeEdge(origin_point, section.right_pt).Edge()
                ais = display.DisplayShape(right_edge)'''


    @staticmethod
    def get_nearest_intersection(edge, section):
        nearest_param = None
        edge_curve = BRepAdaptor_Curve(edge)
        for element_section in section.get_elementsection_list():
            param = SectionAnalyzer.nearest_element_intersection(edge, element_section)
            if param:
                if not nearest_param or nearest_param > param:
                    nearest_param = param
        if nearest_param:
            point = edge_curve.Value(nearest_param)
        else:
            last_param = edge_curve.LastParameter()
            point = edge_curve.Value(last_param)
        return point

    @staticmethod
    def nearest_element_intersection(edge, element_section):
        nearest_param = None
        if not element_section.is_decomposed:
            for shape_section in element_section.shapes_section:
                for shape in shape_section[0]:
                    exp = TopExp_Explorer(shape, TopAbs_EDGE)
                    while exp.More():
                        shape_edge = topods.Edge(exp.Current())
                        intersection = IntTools_EdgeEdge(edge, shape_edge)
                        intersection.Perform()
                        if intersection.IsDone():
                            commonparts = intersection.CommonParts()
                            for i in range(commonparts.Length()):
                                commonpart = commonparts.Value(i + 1)
                                parameter = commonpart.VertexParameter1()
                                if not nearest_param or nearest_param > parameter:
                                    nearest_param = parameter
                        exp.Next()
        else:  # element is decomposed
            for child in element_section.children:
                param = SectionAnalyzer.nearest_element_intersection(edge, child)
                if param:
                    if not nearest_param or nearest_param > param:
                        nearest_param = param
        return nearest_param

    def show_section_wire(self, is_show_section):
        display = self._visualizer.canvas.get_display()
        for section in self.section_list:
            section.set_visible(display, is_show_section)


