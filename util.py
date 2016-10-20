from OCC.Quantity import Quantity_TOC_RGB, Quantity_Color
from math import fabs

from xml.etree import ElementTree
from xml.dom import minidom


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

class Color:
    def __init__(self):
        pass

    white = 255, 255, 255
    gray = 127, 127, 127
    dark_gray = 32, 32, 32

    ais_yellow = Quantity_Color(1, 1, 0, Quantity_TOC_RGB)
    ais_blue = Quantity_Color(0, 0, 1, Quantity_TOC_RGB)
    ais_green = Quantity_Color(0, 1, 0, Quantity_TOC_RGB)
    ais_red = Quantity_Color(1, 0, 0, Quantity_TOC_RGB)

    @staticmethod
    def from_factor_to_rgb(r_factor, g_factor, b_factor):
        r = int(r_factor*255)
        g = int(g_factor*255)
        b = int(b_factor*255)
        return r,g,b

    @staticmethod
    def from_rgb_to_factor(r, g, b):
        r_factor = float(r)/255
        g_factor = float(g)/255
        b_factor = float(b)/255
        return r_factor, g_factor, b_factor

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
            results = value/fabs(value) * (fabs(value)//divider)
            return results

    @staticmethod
    def drange(start, stop, step):
        float_list = []
        r = start
        print start
        print stop
        print step
        while r < stop-step:
            float_list.append(r)
            r += step
        return float_list