from OCC.gp import gp_Pnt, gp_Trsf, gp_Dir, gp_Ax1
from geom import *
from util import *
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
        self.min_horizontal_clearance = self._parent.min_horizontal_clearance
        self.horizontal_dimension_edge_list = []
        self.vertical_dimension_edge_list = []
        self.horizontal_dimension_num_list = []
        self.vertical_dimension_num_list = []
        self.horizontal_dimension_edge_ais_list = []
        self.vertical_dimension_edge_ais_list = []
        self.bounding_rect = [self.path_elevation, self.path_elevation, 0.0, 0.0]  # [minz, maxz, minx, maxx]

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
        print(self.bounding_rect)

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
                self.create_display_edges(display, self.horizontal_dimension_edge_list, self.horizontal_dimension_edge_ais_list, Color.ais_green)
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
        self.section_num = len(self.section_list)
        self.bottom_surface = None
        self.right_surface = None
        self.upper_surface = None
        self.left_surface = None
        self.sampling_distance = None
        self.left_lines = None

    def perform(self, sampling_distance):
        self.sampling_distance = sampling_distance
        self.bottom_surface_analysis()
        self.right_surface_analysis()
        self.left_surface_analysis()
        self.upper_surface_analysis()

    def bottom_surface_analysis(self):
        self.bottom_surface = []
        domain_start = Math.integer_division(self.bounding_rect[2], self.sampling_distance)  # left
        domain_end = Math.integer_division(self.bounding_rect[3], self.sampling_distance)  # right
        for i in range(self.section_num):
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
        for i in range(self.section_num):
            y = i * self.section_distance
            section = self.section_list[i]
            self.right_surface.append([])
            for j in range(int(domain_start), int(domain_end + 1)):
                z = j * self.sampling_distance
                origin_pt = gp_Pnt(0, y, z)
                next_pt = gp_Pnt(self.domain_length, y, z)
                edge = create_edge_from_two_point(origin_pt, next_pt)
                point = PointObject.create(self, edge, section, Orientation.right)
                self.right_surface[i].append(point)


    def upper_surface_analysis(self):
        self.upper_surface = []
        domain_start = Math.integer_division(self.bounding_rect[2], self.sampling_distance)  # left
        domain_end = Math.integer_division(self.bounding_rect[3], self.sampling_distance)  # right
        for i in range(self.section_num):
            y = i * self.section_distance
            section = self.section_list[i]
            self.upper_surface.append([])
            for j in range(int(domain_start), int(domain_end + 1)):
                x = j * self.sampling_distance
                origin_pt = gp_Pnt(x, y, self.path_elevation)
                next_pt = gp_Pnt(x, y, self.path_elevation + self.domain_length)
                edge = create_edge_from_two_point(origin_pt, next_pt)
                point = PointObject.create(self, edge, section, Orientation.up)
                self.upper_surface[i].append(point)

    def left_surface_analysis(self):
        self.left_surface = []
        domain_start = Math.integer_division(self.bounding_rect[0], self.sampling_distance)
        domain_end = Math.integer_division(self.bounding_rect[1], self.sampling_distance)
        for i in range(self.section_num):
            y = i * self.section_distance
            section = self.section_list[i]
            self.left_surface.append([])
            for j in range(int(domain_start), int(domain_end + 1)):
                z = j * self.sampling_distance
                origin_pt = gp_Pnt(0, y, z)
                next_pt = gp_Pnt(-self.domain_length, y, z)
                edge = create_edge_from_two_point(origin_pt, next_pt)
                point = PointObject.create(self, edge, section, Orientation.left)
                self.left_surface[i].append(point)

    def display_surface_point(self, display, is_show_analysis):
        self.display_bottom_surface(display, is_show_analysis)
        self.display_right_surface(display, is_show_analysis)
        self.display_left_surface(display, is_show_analysis)
        self.display_upper_surface(display, is_show_analysis)
        display.Repaint()

    def display_bottom_surface(self, display, is_show_analysis):
        for i in range(len(self.bottom_surface)):
            for j in range(len(self.bottom_surface[i])):
                if self.bottom_surface[i][j]:
                    self.bottom_surface[i][j].display_point(display, is_show_analysis)

    def display_upper_surface(self, display, is_show_analysis):
        for i in range(len(self.upper_surface)):
            for j in range(len(self.upper_surface[i])):
                if self.upper_surface[i][j]:
                    self.upper_surface[i][j].display_point(display, is_show_analysis)

    def display_left_surface(self, display, is_show_analysis):
        for i in range(len(self.left_surface)):
            for j in range(len(self.left_surface[i])):
                if self.left_surface[i][j]:
                    self.left_surface[i][j].display_point(display, is_show_analysis)

    def display_right_surface(self, display, is_show_analysis):
        for i in range(len(self.right_surface)):
            for j in range(len(self.right_surface[i])):
                if self.right_surface[i][j]:
                    self.right_surface[i][j].display_point(display, is_show_analysis)


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
        du, dv = self.get_dimension()
        rect = create_rectangle_from_center(self.point, du, dv, self.orientation)
        self.point_ais = display.DisplayShape(rect, transparency=transparency)
        self.point_ais.GetObject().SetColor(ais_color)

    def get_dimension(self):
        section_distance = self.parent.section_distance
        sampling_distance = self.parent.sampling_distance
        return sampling_distance, section_distance


class ClearanceAnalysis(object):
    def __init__(self, parent):
        self._parent = parent
        self.surface_analysis = self._parent.surface_analysis
        self.section_num = self.surface_analysis.section_num
        self.section_distance = self.surface_analysis.section_distance
        self.sampling_distance = self.surface_analysis.sampling_distance
        self.max_height = None
        self.horizontal_clearance = None
        self.vertical_clearance = None
        self.vertical_clearance_min = None
        self.vertical_clearance_max = None

    def perform(self, max_height):
        self.vertical_clearance = []
        self.horizontal_clearance = []
        self.max_height = max_height
        for i in range(self.section_num): #analyse each section
            self.vertical_clearance.append([])
            bottom_section = self.surface_analysis.bottom_surface[i]
            upper_section = self.surface_analysis.upper_surface[i]
            left_section = self.surface_analysis.left_surface[i]
            right_section = self.surface_analysis.right_surface[i]
            min_z = None
            for j in range(len(bottom_section)):
                bottom_point = bottom_section[j]
                upper_point = upper_section[j]
                if bottom_point:
                    if not min_z or min_z > bottom_point.point.Z():
                        min_z = bottom_point.point.Z()
                if upper_point and bottom_point:
                    vertical_distance = (upper_point.point.Z() - bottom_point.point.Z()), bottom_point
                else:
                    vertical_distance = None
                if vertical_distance:
                    if not self.vertical_clearance_min or self.vertical_clearance_min > vertical_distance[0]:
                        self.vertical_clearance_min = vertical_distance[0]
                    if not self.vertical_clearance_max or self.vertical_clearance_max < vertical_distance[0]:
                        self.vertical_clearance_max = vertical_distance[0]
                self.vertical_clearance[i].append(vertical_distance)
            clearance_limit = min_z + self.max_height
            print(min_z)
            print(clearance_limit)
            max_left = None
            min_right = None
            for k in range(len(bottom_section)):
                left_point = None
                right_point = None
                if k < len(left_section):
                    left_point = left_section[k]
                if k < len(right_section):
                    right_point = right_section[k]
                if left_point:
                    if left_point.point.Z() <= clearance_limit:
                        if not max_left or max_left < left_point.point.X():
                            max_left = left_point.point.X()
                if right_point:
                    if right_point.point.Z() <= clearance_limit:
                        if not min_right or min_right > right_point.point.X():
                            min_right = right_point.point.X()
            self.horizontal_clearance.append((max_left, min_right))

