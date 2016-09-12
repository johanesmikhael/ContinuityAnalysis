from OCC.TColgp import TColgp_Array1OfPnt
from OCC.TColStd import TColStd_Array1OfReal
from OCC.TColStd import TColStd_Array1OfInteger
from OCC.Geom import Geom_BezierCurve
from OCC.Geom import Geom_BSplineCurve

import collections


def divide_range(start, stop, divide_num):
    float_list = []
    r = start
    step = (stop - start) / divide_num
    while r < stop:
        float_list.append(r)
        r += step
    float_list.append(stop)
    return float_list


def points_to_bezier_curve(points):
    pts = TColgp_Array1OfPnt(0, len(points) - 1)
    for n, ptn in enumerate(points):
        pts.SetValue(n, ptn[0])
    crv = Geom_BezierCurve(pts)
    return crv


def points_to_bspline_curve(points, degree):
    pts = TColgp_Array1OfPnt(0, len(points) - 1)
    for n, ptn in enumerate(points):
        if isinstance(ptn, collections.Sequence):
            pts.SetValue(n, ptn[0])
        else:
            pts.SetValue(n, ptn)
    if len(points) == 3:
        if degree > 2:
            degree = 2
    if len(points) == 2:
        if degree > 1:
            degree = 1
    knots_size = len(points) + degree + 1
    knot_sum = degree + 1
    mult_array = [degree + 1]
    while knot_sum < knots_size - (degree + 1):
        knot_sum += 1
        mult_array.append(1)
    mult_array.append(knots_size - knot_sum)
    knot_array = divide_range(0.0, 1.0, len(mult_array)-1)
    print knots_size
    print mult_array
    print knot_array
    knots = TColStd_Array1OfReal(0, len(mult_array) - 1)
    mult = TColStd_Array1OfInteger(0, len(mult_array) - 1)
    i = 0.0
    for n in range(0, len(mult_array)):
        print n
        mult.SetValue(n, mult_array[n])
        knots.SetValue(n, knot_array[n])
        i += 1.0
    crv = Geom_BSplineCurve(pts, knots, mult, degree, False)
    return crv
