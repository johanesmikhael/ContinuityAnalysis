from OCC.GProp import GProp_GProps
from OCC import BRepGProp
from OCC.Bnd import Bnd_Box
from OCC.BRepBndLib import brepbndlib_Add
import OCC.Quantity
from OCC.AIS import AIS_Shape
import OCC.Aspect
from geom import *
from util import Color
from copy import copy


class SliceBoundingBox(object):
    def __init__(self, *args):
        parent, element_slice, is_decomposed = args
        self._parent = parent
        self.bounding_box = None
        self.ais = None
        self.center = None
        self.position = None  # 0 = left, 1 = right, 2 = bottom, 3 = above
        self.side_center = None
        self.element = element_slice.element
        self.material = None
        self.topods = None
        self.process_bounding_box(element_slice, is_decomposed)

    def create_topods(self):
        if self.position == 0:
            self.topods = self.get_right_face(self.bounding_box)
        if self.position == 1:
            self.topods = self.get_left_face(self.bounding_box)
        if self.position == 2:
            self.topods = self.get_upper_face(self.bounding_box)
        if self.position == 3:
            self.topods = self.get_bottom_face(self.bounding_box)
        if self.position is None:
            self.topods = self.get_box(self.bounding_box)

    def display_item(self):
        display = self._parent.get_parent().get_visualizer().canvas.get_display()
        color = self.material.get_surface_colour()
        ais_color = OCC.Quantity.Quantity_Color(color[0], color[1], color[2], OCC.Quantity.Quantity_TOC_RGB)
        transparency = self.material.get_transparency()
        ais_object = AIS_Shape(self.topods)
        ais_object.SetCurrentFacingModel(OCC.Aspect.Aspect_TOFM_BOTH_SIDE)
        ais_object.SetColor(ais_color)
        display.Context.Display(ais_object.GetHandle())
        display.Context.SetTransparency(ais_object.GetHandle(), transparency)
        self.ais = ais_object.GetHandle()

    def process_bounding_box(self, element_slice, is_decomposed):
        print("begin_process_bounding_box")
        if not is_decomposed:
            print("is not undecomposed")
            self.bounding_box = element_slice.bounding_box
            if len(element_slice.shapes_slice) > 0:
                print("analyzing element_sliced %s" % element_slice.name)
                print(self.element)
                material_area_dict = dict()  # begin to measure areas for each material
                for shape_slice in element_slice.shapes_slice:
                    print("analyzing shape %s" % shape_slice)
                    material = shape_slice[1]
                    area = self.get_shape_area(shape_slice[0])
                    print(area)
                    if material in material_area_dict:
                        material_area_dict[material] += area
                    else:
                        material_area_dict[material] = area
                major_material = self.get_major_material(material_area_dict)
                self.material = major_material
        else:
            print("undecomposed")
            self.bounding_box = Bnd_Box()
            material_dict = dict()
            self.analyze_decomposed(element_slice, self.bounding_box, material_dict)
            major_material = self.get_major_material(material_dict)
            self.material = major_material

    def create_bounding_box(self, xmin, ymin, zmin, xmax, ymax, zmax):
        self.bounding_box = Bnd_Box()
        self.bounding_box.Update(xmin, ymin, zmin, xmax, ymax, zmax)

    def set_left_right_side(self, vertical_threshold):
        if self.x_max() < -vertical_threshold:
            self.position = 0
        if self.x_min() > vertical_threshold:
            self.position = 1

    def set_upper_side(self, horizontal_threshold):
        path_elevation = self._parent.get_parent().path_elevation
        if self.z_min() > horizontal_threshold + path_elevation:
            self.position = 3

    def set_bottom_side(self, horizontal_threshold):
        path_elevation = self._parent.get_parent().path_elevation
        if self.z_max() < - horizontal_threshold + path_elevation:
            self.position = 2

    def x_min(self):
        if self.bounding_box:
            return self.bounding_box.CornerMin().X()

    def y_min(self):
        if self.bounding_box:
            return self.bounding_box.CornerMin().Y()

    def set_y_min(self, y_min_new):
        x_min, y_min, z_min, x_max, y_max, z_max = self.bounding_box.Get()
        self.bounding_box.Update(x_min, y_min_new, z_min, x_max, y_max, z_max)

    def z_min(self):
        if self.bounding_box:
            return self.bounding_box.CornerMin().Z()

    def x_max(self):
        if self.bounding_box:
            return self.bounding_box.CornerMax().X()

    def y_max(self):
        if self.bounding_box:
            return self.bounding_box.CornerMax().Y()

    def set_y_max(self, y_max_new):
        x_min, y_min, z_min, x_max, y_max, z_max = self.bounding_box.Get()
        self.bounding_box.Update(x_min, y_min, z_min, x_max, y_max_new, z_max)

    def z_max(self):
        if self.bounding_box:
            return self.bounding_box.CornerMax().Z()

    def copy(self):
        return copy(self)

    def show(self):
        display = self._parent.get_parent().get_visualizer().canvas.get_display()
        display.Context.Display(self.ais)

    def hide(self):
        display = self._parent.get_parent().get_visualizer().canvas.get_display()
        display.Context.Erase(self.ais)

    def is_connect(self, item):
        bnd_box1 = self.bounding_box
        bnd_box2 = item.bounding_box
        is_out = bnd_box1.IsOut(bnd_box2)
        return not is_out
        # is_adjacent_h = is_adjacent_horizontal(bnd_box1, bnd_box2)
        # is_adjacent_v = is_adjacent_vertical(bnd_box1, bnd_box2)
        # if is_adjacent_h or is_adjacent_v:
        #     return True
        # else:
        #     return False

    def is_adjacent_horizontal(self, item):
        bnd_box1 = self.bounding_box
        bnd_box2 = item.bounding_box
        is_adjacent_h = is_adjacent_horizontal(bnd_box1, bnd_box2)
        if is_adjacent_h:
            return True
        else:
            return False

    def distance(self, item):
        bnd_box1 = self.bounding_box
        bnd_box2 = item.bounding_box
        return bnd_box1.Distance(bnd_box2)

    def get_color_distance(self, item):
        material1 = self.material.get_surface_colour()
        material2 = item.material.get_surface_colour()
        distance = Color.colour_distance(material1,material2)
        return distance


    @staticmethod
    def get_shape_area(shape_list):
        area = 0
        for shape in shape_list:
            system = GProp_GProps()
            BRepGProp.brepgprop_SurfaceProperties(shape["topods_shape"], system)
            area += system.Mass()
        return area

    @staticmethod
    def get_major_material(material_area_dict):
        major_material = None
        major_area = 0
        for key in material_area_dict:
            if material_area_dict[key] > major_area:
                major_area = material_area_dict[key]
                major_material = key
        print(major_material.name)
        return major_material

    @staticmethod
    def analyze_decomposed(element_slice, bounding_box, material_dict):
        if element_slice.is_decomposed:
            print(element_slice.name)
            for child in element_slice.children:
                SliceBoundingBox.analyze_decomposed(child, bounding_box, material_dict)
        else:
            for shape_slice in element_slice.shapes_slice:
                print("analysing shape_slice in analyze_decomposed %s" % shape_slice)
                material = shape_slice[1]
                area = SliceBoundingBox.get_shape_area(shape_slice[0])
                for shape in shape_slice[0]:
                    brepbndlib_Add(shape["topods_shape"], bounding_box)
                if material in material_dict:
                    material_dict[material] += area
                else:
                    material_dict[material] = area

    @staticmethod
    def get_right_face(bounding_box):
        corner_min = bounding_box.CornerMin()
        corner_max = bounding_box.CornerMax()
        y_min = corner_min.Y()
        z_min = corner_min.Z()
        x_max = corner_max.X()
        y_max = corner_max.Y()
        z_max = corner_max.Z()
        p1 = gp_Pnt(x_max, y_min, z_min)
        p2 = gp_Pnt(x_max, y_max, z_min)
        p3 = gp_Pnt(x_max, y_max, z_max)
        p4 = gp_Pnt(x_max, y_min, z_max)
        bounding_box_surface = create_rectangular_face(p1, p2, p3, p4)
        return bounding_box_surface

    @staticmethod
    def get_left_face(bounding_box):
        corner_min = bounding_box.CornerMin()
        corner_max = bounding_box.CornerMax()
        x_min = corner_min.X()
        y_min = corner_min.Y()
        z_min = corner_min.Z()
        y_max = corner_max.Y()
        z_max = corner_max.Z()
        p1 = gp_Pnt(x_min, y_min, z_min)
        p2 = gp_Pnt(x_min, y_min, z_max)
        p3 = gp_Pnt(x_min, y_max, z_max)
        p4 = gp_Pnt(x_min, y_max, z_min)
        bounding_box_surface = create_rectangular_face(p1, p2, p3, p4)
        return bounding_box_surface

    @staticmethod
    def get_upper_face(bounding_box):
        corner_min = bounding_box.CornerMin()
        corner_max = bounding_box.CornerMax()
        x_min = corner_min.X()
        y_min = corner_min.Y()
        z_min = corner_min.Z()
        x_max = corner_max.X()
        y_max = corner_max.Y()
        z_max = corner_max.Z()
        p1 = gp_Pnt(x_min, y_min, z_max)
        p2 = gp_Pnt(x_max, y_min, z_max)
        p3 = gp_Pnt(x_max, y_max, z_max)
        p4 = gp_Pnt(x_min, y_max, z_max)
        bounding_box_surface = create_rectangular_face(p1, p2, p3, p4)
        return bounding_box_surface

    @staticmethod
    def get_bottom_face(bounding_box):
        corner_min = bounding_box.CornerMin()
        corner_max = bounding_box.CornerMax()
        x_min = corner_min.X()
        y_min = corner_min.Y()
        z_min = corner_min.Z()
        x_max = corner_max.X()
        y_max = corner_max.Y()
        z_max = corner_max.Z()
        p1 = gp_Pnt(x_min, y_min, z_min)
        p2 = gp_Pnt(x_min, y_max, z_min)
        p3 = gp_Pnt(x_max, y_max, z_min)
        p4 = gp_Pnt(x_max, y_min, z_min)
        bounding_box_surface = create_rectangular_face(p1, p2, p3, p4)
        return bounding_box_surface

    @staticmethod
    def get_box(bounding_box):
        corner_min = bounding_box.CornerMin()
        corner_max = bounding_box.CornerMax()
        bounding_box_shape = create_box_from_two_points(corner_min, corner_max)
        return bounding_box_shape
