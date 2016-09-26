from OCC.gp import gp_Pnt, gp_Trsf, gp_Dir, gp_Ax1
from geom import create_edge_to_points
from quantity import *


class DimensionAnalysis(object):
    def __init__(self, parent):
        self._parent = parent
        self.section_list = self._parent.section_list
        self.section_distance = self._parent.section_distance
        self.path_elevation = self._parent.path_elevation
        self.domain_length = self._parent.domain_length
        self.horizontal_dimension_edge_list = []
        self.vertical_dimension_edge_list = []
        self.horizontal_dimension_num_list = []
        self.vertical_dimension_num_list = []
        self.horizontal_dimension_edge_ais_list = []
        self.vertical_dimension_edge_ais_list = []

    def perform(self):
        for i, section in enumerate(self.section_list):
            x = i * self.section_distance
            horizontal_points = []
            vertical_points = []
            origin_point = gp_Pnt(x, 0.0, self.path_elevation)
            vertical_points.append(gp_Pnt(x, 0.0, self.path_elevation - self.domain_length))  # bottom
            vertical_points.append(gp_Pnt(x, 0.0, self.path_elevation + self.domain_length))  # upper
            horizontal_points.append(gp_Pnt(x, -self.domain_length, self.path_elevation))  # left
            horizontal_points.append(gp_Pnt(x, self.domain_length, self.path_elevation))  # right
            vertical_edges = create_edge_to_points(origin_point, vertical_points)
            horizontal_edges = create_edge_to_points(origin_point,horizontal_points)
            vertical_section_points = section.get_nearest_intersection_to_edges(vertical_edges)
            horizontal_section_points = section.get_nearest_intersection_to_edges(horizontal_edges)
            self.vertical_dimension_edge_list.append(create_edge_to_points(origin_point, vertical_section_points))
            self.horizontal_dimension_edge_list.append(create_edge_to_points(origin_point, horizontal_section_points))

    def display_dimension_edges(self, display):
        self.display_vertical_edges(display)
        self.display_horizontal_edges(display)
        display.Repaint()

    def display_vertical_edges(self, display):
        self.display_edges(display, self.vertical_dimension_edge_list, self.vertical_dimension_edge_ais_list, Color.ais_blue)

    def display_horizontal_edges(self, display):
        self.display_edges(display, self.horizontal_dimension_edge_list, self.horizontal_dimension_edge_ais_list, Color.ais_red)

    @staticmethod
    def display_edges(display, dimension_edge_list, dimension_edge_ais_list, ais_color):
        for edges in dimension_edge_list:
            edges_ais = []
            for edge in edges:
                ais = display.DisplayShape(edge)
                ais.GetObject().SetColor(ais_color)
                edges_ais.append(ais)
            dimension_edge_ais_list.append(edges_ais)


