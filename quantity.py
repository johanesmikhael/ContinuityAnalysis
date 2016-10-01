from OCC.Quantity import Quantity_TOC_RGB, Quantity_Color
from math import fabs

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