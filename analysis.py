from OCC.gp import gp_Pnt, gp_Trsf, gp_Dir, gp_Ax1
from geom import *
from quantity import *
from OCC.BRepPrimAPI import BRepPrimAPI_MakeSphere
from math import floor, ceil

import OCC.Quantity


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
        self.bounding_rect = [self.path_elevation, 0.0, 0.0, 0.0]  # [minz, maxz, minx, maxx]

    def perform(self):
        for i, section in enumerate(self.section_list):
            y = i * self.section_distance
            horizontal_points = []
            vertical_points = []
            origin_point = gp_Pnt(0.0, y, self.path_elevation)
            vertical_points.append(gp_Pnt(0.0, y, self.path_elevation - self.domain_length))  # bottom
            vertical_points.append(gp_Pnt(0.0, y, self.path_elevation + self.domain_length))  # upper
            horizontal_points.append(gp_Pnt(-self.domain_length, y, self.path_elevation))  # left
            horizontal_points.append(gp_Pnt(self.domain_length, y, self.path_elevation))  # right
            vertical_edges = create_edge_to_points(origin_point, vertical_points)
            horizontal_edges = create_edge_to_points(origin_point,horizontal_points)
            vertical_section_points = section.get_nearest_intersection_to_edges(vertical_edges)
            horizontal_section_points = section.get_nearest_intersection_to_edges(horizontal_edges)
            self.update_vertical_bound(vertical_section_points)
            self.update_horizontal_bound(horizontal_section_points)
            self.vertical_dimension_edge_list.append(create_edge_to_points(origin_point, vertical_section_points))
            self.horizontal_dimension_edge_list.append(create_edge_to_points(origin_point, horizontal_section_points))
        print self.bounding_rect

    def update_vertical_bound(self, vertical_points):
        bottom_pnt = vertical_points[0]
        upper_pnt = vertical_points[1]
        self.bounding_rect[0] = Math.replace_minimum(self.bounding_rect[0], bottom_pnt.Z())
        self.bounding_rect[1] = Math.replace_maximum(self.bounding_rect[1], upper_pnt.Z())

    def update_horizontal_bound(self, horizontal_points):
        left_pnt = horizontal_points[0]
        right_pnt = horizontal_points[1]
        self.bounding_rect[2] = Math.replace_minimum(self.bounding_rect[2], left_pnt.X())
        self.bounding_rect[3] = Math.replace_maximum(self.bounding_rect[3], right_pnt.X())

    def display_dimension_edges(self, display, is_show_analysis):
        self.display_vertical_edges(display, is_show_analysis)
        self.display_horizontal_edges(display, is_show_analysis)
        display.Repaint()

    def display_vertical_edges(self, display, is_show_analysis):
        if is_show_analysis:
            if not len(self.vertical_dimension_edge_ais_list) > 0:
                self.create_display_edges(display, self.vertical_dimension_edge_list, self.vertical_dimension_edge_ais_list, Color.ais_blue)
            else:
                self.display_edges(display, self.vertical_dimension_edge_ais_list, True)
        else:
            self.display_edges(display, self.vertical_dimension_edge_ais_list, False)

    def display_horizontal_edges(self, display, is_show_analysis):
        if is_show_analysis:
            if not len(self.horizontal_dimension_edge_ais_list) > 0:
                self.create_display_edges(display, self.horizontal_dimension_edge_list, self.horizontal_dimension_edge_ais_list, Color.ais_red)
            else:
                self.display_edges(display, self.horizontal_dimension_edge_ais_list, True)
        else:
            self.display_edges(display, self.horizontal_dimension_edge_ais_list, False)

    @staticmethod
    def create_display_edges(display, dimension_edge_list, dimension_edge_ais_list, ais_color):
        for edges in dimension_edge_list:
            edges_ais = []
            for edge in edges:
                ais = display.DisplayShape(edge)
                ais.GetObject().SetColor(ais_color)
                edges_ais.append(ais)
            dimension_edge_ais_list.append(edges_ais)

    @staticmethod
    def display_edges(display, dimension_edge_ais_list, is_show):
        for edge_ais in dimension_edge_ais_list:
            if is_show:
                display.Context.Display(edge_ais)
            else:
                display.Context.Remove(edge_ais)


class SurfaceAnalysis(object):
    def __init__(self, parent):
        self._parent = parent
        self.bounding_rect = parent.dimension_analysis.bounding_rect
        self.section_list = parent.section_list
        self.section_distance = parent.section_distance
        self.path_elevation = parent.path_elevation
        self.domain_length = parent.domain_length
        self.bottom_surface = None
        self.right_surface = None
        self.upper_surface = None
        self.left_surface = None
        self.sampling_distance = None

    def perform(self, sampling_distance):
        self.sampling_distance = sampling_distance
        self.bottom_surface_analysis()

    def bottom_surface_analysis(self):
        self.bottom_surface = []
        domain_start = Math.integer_division(self.bounding_rect[2], self.sampling_distance)  # left
        domain_end = Math.integer_division(self.bounding_rect[3], self.sampling_distance)  # right
        for i in range(len(self.section_list)):
            y = i * self.section_distance
            section = self.section_list[i]
            self.bottom_surface.append([])
            for j in range(int(domain_start), int(domain_end + 1)):
                x = j * self.sampling_distance
                origin_pt = gp_Pnt(x, y, self.path_elevation)
                next_pt = gp_Pnt(x, y, self.path_elevation - self.domain_length)
                edge = create_edge_from_two_point(origin_pt, next_pt)
                point = PointObject.create(self, edge, section, Orientation.bottom)
                self.bottom_surface[i].append(point)

    def right_surface_analysis(self):
        self.right_surface = []
        domain_start = Math.integer_division(self.bounding_rect[0], self.sampling_distance)
        domain_end = Math.integer_division(self.bounding_rect[1], self.sampling_distance)
        for i in range(len(self.section_list)):
            x = i * self.section_distance
            section = self.section_list[i]
            self.right_surface.append([])
            for j in range(int(domain_start), int(domain_end + 1)):
                z = j * self.sampling_distance
                origin_pt = gp_Pnt(x, 0, z)
                next_pt = gp_Pnt(x, 0 + self.domain_length)

    def display_surface_point(self, display, is_show_analysis):
        self.display_bottom_surface(display, is_show_analysis)
        display.Repaint()

    def display_bottom_surface(self, display, is_show_analysis):
        for i in range(len(self.bottom_surface)):
            for j in range(len(self.bottom_surface[i])):
                if self.bottom_surface[i][j]:
                    self.bottom_surface[i][j].display_point(display, is_show_analysis)
        pass


class PointObject(object):
    def __init__(self, *args):
        parent, point, element, material, orientation = args
        self.parent = parent
        self.point = point
        self.element = element
        self.material = material
        self.orientation = orientation
        self.point_ais = None

    @staticmethod
    def create(parent, edge, section, orientation):
        section_point = section.get_nearest_intersection_element(edge)
        if section_point:
            point = section_point[0]
            element = section_point[1].element  # ElementSection.element
            material = section_point[2][1]  # shape_section[1] --> Material
            point_object = PointObject(parent, point, element, material, orientation)
            return point_object
        else:
            return None

    def display_point(self, display, is_show):
        if is_show:
            if not self.point_ais:
                self.create_display_point(display)
            else:
                display.Context.Display(self.point_ais)
        else:
            display.Context.Remove(self.point_ais)

    def create_display_point(self, display):
        ais_color = OCC.Quantity.Quantity_Color(0.1, 0.1, 0.1, OCC.Quantity.Quantity_TOC_RGB)
        transparency = 0
        if self.material is not None:
            color = self.material.get_shading_colour()
            ais_color = OCC.Quantity.Quantity_Color(color[0], color[1], color[2], OCC.Quantity.Quantity_TOC_RGB)
            transparency = self.material.get_transparency()
        # du, dv = self.get_dimension()
        # rect = create_rectangle_from_center(self.point, du, dv, self.orientation)
        self.point_ais = display.DisplayShape(self.point, transparency=transparency)
        self.point_ais.GetObject().SetColor(ais_color)

    def get_dimension(self):
        section_distance = self.parent.section_distance
        sampling_distance = self.parent.sampling_distance
        return sampling_distance, section_distance

