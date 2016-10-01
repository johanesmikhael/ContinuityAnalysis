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
        self.surface_analysis = None

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
            translation = self.get_translation(section_plane_pln, i, distance, self.path_elevation)
            rotation = self.get_rotation(section_plane_pln, i, distance, self.path_elevation)
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
        gp_pnt_1 = gp_Pnt(0.0, n*self._visualizer.parent.section_distance, self.path_elevation)
        points = [gp_pnt_0, gp_pnt_1]
        crv = points_to_bspline_curve(points, 1)
        ais = self._visualizer.canvas.get_display().DisplayShape(crv)
        self.section_axis = [crv, ais]

    @staticmethod
    def get_translation(section_plane_pln, n_section, section_distance, height):
        gp_axis_0 = section_plane_pln.Axis()
        gp_point_0 = gp_axis_0.Location()
        gp_point_1 = gp_Pnt(0.0, n_section * section_distance, height)
        gp_trsf = gp_Trsf()
        gp_trsf.SetTranslation(gp_point_0, gp_point_1)
        return gp_trsf

    @staticmethod
    def get_rotation(section_plane_pln, n_section, section_distance, height):
        gp_axis_0 = section_plane_pln.Axis()
        gp_point_1 = gp_Pnt(0.0, n_section * section_distance, height)
        gp_dir = gp_Dir(0.0, 1.0, 0.0) # toward y axis
        gp_axis_1 = gp_Ax1(gp_point_1, gp_dir)
        rotation_angle = gp_axis_0.Angle(gp_axis_1)
        print rotation_angle
        rotation_axis = gp_Ax1()
        rotation_axis.SetLocation(gp_point_1)
        gp_trsf = gp_Trsf()
        gp_dir_0 = gp_axis_0.Direction()
        if gp_dir_0.X() <= 0:  # the set the rotation direction by determine the axis direction in quadran
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
        self.display_dimension_analysis(True)

    def display_dimension_analysis(self, is_show_analysis):
        display = self._visualizer.canvas.get_display()
        self.dimension_analysis.display_dimension_edges(display, is_show_analysis)

    def analyze_surface(self):
        if self.dimension_analysis:
            self.surface_analysis = SurfaceAnalysis(self)
            self.surface_analysis.perform(0.01)
            self.display_surface_analysis(True)

    def display_surface_analysis(self, is_show_analysis):
        display = self._visualizer.canvas.get_display()
        self.surface_analysis.display_surface_point(display, is_show_analysis)

    def show_section_wire(self, is_show_section):
        display = self._visualizer.canvas.get_display()
        for section in self.section_list:
            section.set_visible(display, is_show_section)


