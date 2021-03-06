from OCC.Quantity import Quantity_TOC_RGB, Quantity_Color
from math import fabs

from xml.etree import ElementTree
from xml.dom import minidom

from PyQt5.QtGui import QColor
from colorsys import *

import os
from OCC.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Interface import Interface_Static_SetCVal
from OCC.IFSelect import IFSelect_RetDone
import networkx as nx
from matplotlib import pyplot, patches
import numpy as np


def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def get_text_from_xml(node):
    return node.childNodes[0].data


def get_float_from_xml(node):
    text = get_text_from_xml(node)
    return float(text)


def get_int_from_xml(node):
    float_value = get_float_from_xml(node)
    return int(float_value)


def write_step_file(a_shape, filename, application_protocol="AP203"):
    """ exports a shape to a STEP file
    a_shape: the topods_shape to export (a compound, a solid etc.)
    filename: the filename
    application protocol: "AP203" or "AP214"
    """
    # a few checks
    if a_shape.IsNull():
        raise AssertionError("Shape %s is null." % a_shape)
    if application_protocol not in ["AP203", "AP214IS"]:
        raise AssertionError("application_protocol must be either AP203 or AP214IS. You passed %s." % application_protocol)
    if os.path.isfile(filename):
        print("Warning: %s file already exists and will be replaced" % filename)
    # creates and initialise the step exporter
    step_writer = STEPControl_Writer()
    Interface_Static_SetCVal("write.step.schema", application_protocol)

    # transfer shapes and write file
    step_writer.Transfer(a_shape, STEPControl_AsIs)
    status = step_writer.Write(filename)

    if not status == IFSelect_RetDone:
        raise AssertionError("Error while writing shape to STEP file.")
    if not os.path.isfile(filename):
        raise AssertionError("File %s was not saved to filesystem." % filename)


def create_folder(folder):
    try:
        os.mkdir(folder)
    except OSError:
        print("Creation of the directory %s failed" % folder)
        return False
    else:
        print("Successfully created the directory %s " % folder)
        return True

class Color:
    def __init__(self):
        pass

    white = 255, 255, 255
    gray = 127, 127, 127
    green = 0, 240, 0
    red = 240, 0, 0
    dark_gray = 32, 32, 32
    dark_green = 0, 128, 0
    dark_red = 128, 0, 0

    ais_yellow = Quantity_Color(1, 1, 0, Quantity_TOC_RGB)
    ais_blue = Quantity_Color(0, 0, 1, Quantity_TOC_RGB)
    ais_green = Quantity_Color(0, 1, 0, Quantity_TOC_RGB)
    ais_red = Quantity_Color(1, 0, 0, Quantity_TOC_RGB)

    @staticmethod
    def from_factor_to_rgb(r_factor, g_factor, b_factor):
        r = int(r_factor * 255)
        g = int(g_factor * 255)
        b = int(b_factor * 255)
        return r, g, b

    @staticmethod
    def from_rgb_to_factor(r, g, b):
        r_factor = float(r) / 255
        g_factor = float(g) / 255
        b_factor = float(b) / 255
        return r_factor, g_factor, b_factor

    @staticmethod
    def create_qcolor_from_rgb_tuple(rgb_tuple):
        color = QColor(rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])
        return color

    @staticmethod
    def create_qcolor_from_rgb_tuple_f(rgb):
        rgb_tuple = Color.from_factor_to_rgb(rgb[0], rgb[1], rgb[2])
        color = Color.create_qcolor_from_rgb_tuple(rgb_tuple)
        return color

    @staticmethod
    def colour_distance(rgb_tuple1, rgb_tuple2):
        squared_distance = Color.squared_colour_distance(rgb_tuple1, rgb_tuple2)
        return pow(squared_distance, 0.5)

    @staticmethod
    def squared_colour_distance(rgb_tuple1, rgb_tuple2):
        print("start calc squared distance")
        print(rgb_tuple1)
        print(rgb_tuple2)
        squared_distance = (rgb_tuple2[0] - rgb_tuple1[0]) ** 2 + \
                           (rgb_tuple2[1] - rgb_tuple1[1]) ** 2 + \
                           (rgb_tuple2[2] - rgb_tuple1[2]) ** 2
        print(squared_distance)
        return squared_distance



class ColorInterpolation(object):
    def __init__(self, *args):
        self.start_color = args[0]  # qcolor
        self.end_color = args[1]  # qcolor
        self.min_value = args[2]
        self.max_value = args[3]
        self.hsv_start = self.get_hsv_from_qcolor(self.start_color)
        self.hsv_end = self.get_hsv_from_qcolor(self.end_color)

    @staticmethod
    def get_hsv_from_qcolor(qcolor):
        r = qcolor.redF()
        g = qcolor.greenF()
        b = qcolor.blueF()
        hsv_value = rgb_to_hsv(r, g, b)
        return hsv_value

    def get_interpolation_from_value(self, value):
        if value <= self.min_value:
            return self.start_color
        elif value >= self.max_value:
            return self.end_color
        else:  # the value is in beetween the value comain
            min_hue = self.hsv_start[0]
            max_hue = self.hsv_end[0]
            min_saturation = self.hsv_start[1]
            max_saturation = self.hsv_end[1]
            min_value = self.hsv_start[2]
            max_value = self.hsv_end[2]
            fraction = (value - self.min_value) / (self.max_value - self.min_value)
            hue = fraction * (max_hue - min_hue) + min_hue
            saturation = fraction * (max_saturation - min_saturation) + min_saturation
            value = fraction * (max_value - min_value) + min_value
            if hue < 0:
                hue = 0
            elif hue > 1:
                hue = 1
            if saturation < 0:
                saturation = 0
            elif saturation > 1:
                saturation = 1
            if value < 0:
                value = 0
            elif value > 1:
                value = 1
            rgb = hsv_to_rgb(hue, saturation, value)
            color_interpolation = Color.create_qcolor_from_rgb_tuple_f(rgb)
            return color_interpolation


class Orientation:
    def __init__(self):
        pass

    bottom = 0
    up = 1
    left = 2
    right = 3


class Math:
    def __init__(self):
        pass

    @staticmethod
    def replace_minimum(compared_value, value):
        if value < compared_value:
            compared_value = value
        return compared_value

    @staticmethod
    def replace_maximum(compared_value, value):
        if value > compared_value:
            compared_value = value
        return compared_value

    @staticmethod
    def integer_division(value, divider):
        if value >= 0:
            results = value // divider
            return results
        else:
            results = value / fabs(value) * (fabs(value) // divider)
            return results

    @staticmethod
    def drange(start, stop, step):
        float_list = []
        r = start
        print(start)
        print(stop)
        print(step)
        while r < stop - step:
            float_list.append(r)
            r += step
        return float_list
