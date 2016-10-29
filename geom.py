from OCC.TColgp import TColgp_Array1OfPnt
from OCC.TColStd import TColStd_Array1OfReal
from OCC.TColStd import TColStd_Array1OfInteger
from OCC.Geom import Geom_BezierCurve
from OCC.Geom import Geom_BSplineCurve
from OCC.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
from OCC.BRepBuilderAPI import BRepBuilderAPI_MakePolygon
from OCC.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCC.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.GeomAdaptor import GeomAdaptor_Curve
from OCC.GCPnts import GCPnts_AbscissaPoint
from OCC.gp import gp_Pnt
from util import *
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
    print(knots_size)
    print(mult_array)
    print(knot_array)
    knots = TColStd_Array1OfReal(0, len(mult_array) - 1)
    mult = TColStd_Array1OfInteger(0, len(mult_array) - 1)
    i = 0.0
    for n in range(0, len(mult_array)):
        print(n)
        mult.SetValue(n, mult_array[n])
        knots.SetValue(n, knot_array[n])
        i += 1.0
    crv = Geom_BSplineCurve(pts, knots, mult, degree, False)
    return crv


def create_edge_to_points(origin_point, points):
    edges = []
    for point in points:
        edge = create_edge_from_two_point(origin_point, point)
        edges.append(edge)
    return edges


def create_edge_from_two_point(origin_point, point):
    edge = BRepBuilderAPI_MakeEdge(origin_point, point).Edge()
    return edge


def create_box_from_center(origin_point, dx, dy, dz):
    point_x = origin_point.X() - dx/2
    point_y = origin_point.Y() - dy/2
    point_z = origin_point.Z() - dz/2
    point = gp_Pnt(point_x, point_y, point_z)
    box_shape = BRepPrimAPI_MakeBox(point, dx, dy, dz).Shape()
    return box_shape


def create_rectangle_from_center(origin_point, du, dv, orientation):
    x = origin_point.X()
    y = origin_point.Y()
    z = origin_point.Z()
    if orientation == Orientation.bottom:
        p1 = gp_Pnt(x-du/2, y-dv/2,z)
        p2 = gp_Pnt(x-du/2, y+dv/2,z)
        p3 = gp_Pnt(x+du/2, y+dv/2,z)
        p4 = gp_Pnt(x+du/2, y-dv/2,z)
    elif orientation == Orientation.up:
        p1 = gp_Pnt(x-du/2, y+dv/2,z)
        p2 = gp_Pnt(x-du/2, y-dv/2,z)
        p3 = gp_Pnt(x+du/2, y-dv/2,z)
        p4 = gp_Pnt(x+du/2, y+dv/2,z)
    elif orientation == Orientation.right:
        p1 = gp_Pnt(x, y-dv/2, z+du/2)
        p2 = gp_Pnt(x, y-dv/2, z-du/2)
        p3 = gp_Pnt(x, y+dv/2, z-du/2)
        p4 = gp_Pnt(x, y+dv/2, z+du/2)
    elif orientation == Orientation.left:
        p1 = gp_Pnt(x, y-dv/2, z-du/2)
        p2 = gp_Pnt(x, y-dv/2, z+du/2)
        p3 = gp_Pnt(x, y+dv/2, z+du/2)
        p4 = gp_Pnt(x, y+dv/2, z-du/2)
    wire = BRepBuilderAPI_MakePolygon(p1, p2, p3, p4, True).Wire()
    rectangle_face = BRepBuilderAPI_MakeFace(wire).Face()
    return rectangle_face


def divide_curve(crv, distance):
    geom_adaptor_curve = GeomAdaptor_Curve(crv.GetHandle())
    curve_param = [0.0]
    param = 0
    while param < 1:
        gcpnts_abscissa_point = GCPnts_AbscissaPoint(geom_adaptor_curve, distance, param)
        param = gcpnts_abscissa_point.Parameter()
        if param <= 1:
            curve_param.append(param)
    return curve_param


def curve_length(crv, param1, param2):
    geom_adaptor_curve = GeomAdaptor_Curve(crv.GetHandle())
    length = GCPnts_AbscissaPoint.Length(geom_adaptor_curve, param1, param2)
    return length
