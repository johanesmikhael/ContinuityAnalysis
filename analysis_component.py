
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsItemGroup, QGraphicsLineItem
from PyQt5.QtWidgets import QGraphicsSimpleTextItem, QGraphicsRectItem
from PyQt5.QtCore import qAbs, QLineF, QPointF, qrand, QRectF, QSizeF, qsrand, Qt, QTime
from PyQt5.QtGui import QPen, QColor, QBrush
from util import Math
from util import Color, ColorInterpolation


class BaseGraphic(QGraphicsItemGroup):
    def __init__(self, *args):
        super(BaseGraphic, self).__init__()
        self.label = args[3]
        self.parent = args[0]
        self.section_analyzer = self.parent.section_analyzer
        self.width = None
        self.height = None
        self.margin = None
        self.position = args[1], args[2]
        self.content_width = None
        self.content_height = None
        self.distance_pointer = None
        self.distance_label = None
        self.section_num = len(self.section_analyzer.section_list)
        self.section_distance = self.section_analyzer.section_distance
        self.length_multiplier = 100.0
        self.height_multiplier = 100.0
        self.line_extend = 10
        self.margin = 30
        self._inited = False

    def create_distance_pointer(self):
        self.distance_pointer = QGraphicsLineItem()
        pen = QPen()
        pen.setWidthF(0.5)
        pen.setStyle(Qt.DashDotLine)
        self.distance_pointer.setPen(pen)
        self.distance_pointer.setZValue(1.0)
        self.addToGroup(self.distance_pointer)
        self.distance_label = QGraphicsSimpleTextItem()
        self.distance_label.setZValue(1.0)
        self.addToGroup(self.distance_label)


    def init_dimension(self):
        section_num = len(self.section_analyzer.section_list)
        section_distance = self.section_analyzer.section_distance
        self.content_width = section_num * section_distance * self.length_multiplier
        self.create_distance_pointer()
        self._inited = True

    def update_graph_size(self):
        if self.content_height and self.content_width:
            self.width = self.content_width + self.margin * 2
            self.height = self.content_height + self.margin * 2
        bounding_rect = self.boundingRect()
        # bounding_rect.setWidth(self.width)
        # bounding_rect.setHeight(self.height)

    def set_distance_pointer(self, distance):
        if self._inited:
            x1 = self.position[0] + self.margin + distance * self.length_multiplier
            y1 = self.position[1]
            x2 = x1
            y2 = y1 + self.height
            self.distance_pointer.setLine(x1, y1, x2, y2)
            self.distance_label.setText("%.2f" % distance)
            self.distance_label.setPos(x2,y2)
        pass

    @staticmethod
    def set_rect_fill(*args):
        if args[0] == 0: #surface color mode
            rect = args[1]
            color = args[2]
            qcolor = Color.create_qcolor_from_rgb_tuple_f(color)
            brush = QBrush(qcolor)
            rect.setBrush(brush)


class ClearanceWidthGraph(BaseGraphic):
    def __init__(self, *args):
        super(ClearanceWidthGraph, self).__init__(*args)
        self.dimension_analysis = self.section_analyzer.dimension_analysis
        self.clearance_analysis = self.section_analyzer.clearance_analysis
        self.min_horizontal_clearance = self.dimension_analysis.min_horizontal_clearance
        self.graph_zero = [None, None]
        self.graph_end = [None, None]
        self.clearance_label = QGraphicsSimpleTextItem()
        self.addToGroup(self.clearance_label)
        self.clearance_label.setZValue(1.0)
        self.init_dimension()

    def init_dimension(self):
        super(ClearanceWidthGraph, self).init_dimension()
        height_start = self.dimension_analysis.bounding_rect[2]
        height_end = self.dimension_analysis.bounding_rect[3]
        self.content_height = (height_end - height_start) * self.height_multiplier
        self.update_graph_size()
        self.create_axis()
        self.create_scale()
        self.add_clearance_graph()

    def create_axis(self):
        bounding_end = abs(self.dimension_analysis.bounding_rect[3])
        bounding_start = abs(self.dimension_analysis.bounding_rect[2])
        pen = QPen()
        pen.setWidthF(0.5)
        # horizontal line
        self.graph_zero[0] = self.position[0] + self.margin - self.line_extend
        self.graph_zero[1] = self.position[1] + bounding_start * self.height_multiplier + self.margin
        self.graph_end[0] = self.graph_zero[0] + self.content_width + self.line_extend
        self.graph_end[1] = self.graph_zero[1]
        line_item_horizontal = QGraphicsLineItem(self.graph_zero[0], self.graph_zero[1], self.graph_end[0], self.graph_end[1])
        line_item_horizontal.setPen(pen)
        self.addToGroup(line_item_horizontal)
        center = (self.graph_zero[0] + self.line_extend), self.graph_zero[1]
        y_top = center[1] - (bounding_start*self.height_multiplier)
        y_bottom = center[1]+(bounding_end*self.height_multiplier)
        line_item_vertical = QGraphicsLineItem(center[0], y_top, center[0], y_bottom)
        line_item_vertical.setPen(pen)
        self.addToGroup(line_item_vertical)
        pen_thin = QPen()
        pen_thin.setWidthF(0.2)
        start_graph = center[1] - 10
        while start_graph > center[1] - bounding_start * self.height_multiplier:
            line_item_horizontal = QGraphicsLineItem(self.graph_zero[0], start_graph, self.graph_end[0], start_graph)
            line_item_horizontal.setPen(pen_thin)
            line_item_horizontal.setZValue(-0.5)
            self.addToGroup(line_item_horizontal)
            start_graph -= 10
        start_graph = center[1] + 10
        while start_graph < center[1] + bounding_end * self.height_multiplier:
            line_item_horizontal = QGraphicsLineItem(self.graph_zero[0], start_graph, self.graph_end[0], start_graph)
            line_item_horizontal.setPen(pen_thin)
            line_item_horizontal.setZValue(-0.5)
            self.addToGroup(line_item_horizontal)
            start_graph += 10

    def create_scale(self):
        section_num = len(self.section_analyzer.section_list)
        section_distance = self.section_analyzer.section_distance
        total_distance = section_num * section_distance
        div = int(Math.integer_division(total_distance, 1.0))
        print(total_distance)
        for i in range(div+1):
            x = self.graph_zero[0] + i * self.length_multiplier + self.line_extend
            y = self.graph_zero[1]
            scale_text = QGraphicsSimpleTextItem("%.2f" % float(i))
            scale_text.setPos(x, y)
            self.addToGroup(scale_text)

    def add_clearance_graph(self):
        print("-----------------------------------------")
        horizontal_clearance = self.clearance_analysis.horizontal_clearance
        x_init = self.graph_zero[0] + self.line_extend
        y_init = self.graph_zero[1]
        for i in range(len(horizontal_clearance)):
            clearance_points = horizontal_clearance[i]
            x = x_init + i * self.dimension_analysis.section_distance * self.length_multiplier
            left = -self.dimension_analysis.domain_length
            right = self.dimension_analysis.domain_length
            if clearance_points[0]:
                left = clearance_points[0]
            if clearance_points[1]:
                right = clearance_points[1]
            clearance = right - left
            y_top = y_init + left * self.height_multiplier
            y_bottom = y_init + right * self.height_multiplier
            pen_red = QPen()
            red = Color.create_qcolor_from_rgb_tuple(Color.red)
            pen_red.setColor(red)
            pen_green = QPen()
            green = Color.create_qcolor_from_rgb_tuple(Color.green)
            pen_green.setColor(green)
            line = QGraphicsLineItem(x, y_top, x, y_bottom)
            if clearance < self.min_horizontal_clearance:
                line.setPen(pen_red)
            else:
                line.setPen(pen_green)
            self.addToGroup(line)
        pass

    def set_distance_pointer(self, distance):
        horizontal_clearance = self.clearance_analysis.horizontal_clearance
        super(ClearanceWidthGraph, self).set_distance_pointer(distance)
        index = int(distance/self.section_distance)
        clearance = None
        if index < len(horizontal_clearance):
            clearance = horizontal_clearance[index]
        x = self.distance_pointer.line().x1()
        y = self.distance_pointer.line().y1() + (self.distance_pointer.line().y2() - self.distance_pointer.line().y1())/8
        self.clearance_label.setPos(x, y)
        if clearance:
            distance = clearance[1] - clearance[0]
            self.clearance_label.setText("clearance = %.2f" % distance)


class ClearanceHeightGraph(BaseGraphic):
    def __init__(self, *args):
        super(ClearanceHeightGraph, self).__init__(*args)
        self.dimension_analysis = self.section_analyzer.dimension_analysis
        self.clearance_analysis = self.section_analyzer.clearance_analysis
        self.min_horizontal_clearance = self.dimension_analysis.min_horizontal_clearance
        self.graph_zero = [None, None]
        self.graph_end = [None, None]
        self.vertical_clearance_min = self.clearance_analysis.vertical_clearance_min
        self.vertical_clearance_max = self.clearance_analysis.vertical_clearance_max
        self.color_interpolation = None
        self.init_color_interpolation()
        self.init_dimension()

    def init_color_interpolation(self):
        color_start = Color.create_qcolor_from_rgb_tuple(Color.red)
        color_end = Color.create_qcolor_from_rgb_tuple(Color.green)
        self.color_interpolation = ColorInterpolation(color_start, color_end, self.vertical_clearance_min, self.vertical_clearance_max)

    def init_dimension(self):
        super(ClearanceHeightGraph, self).init_dimension()
        height_start = self.dimension_analysis.bounding_rect[2]
        height_end = self.dimension_analysis.bounding_rect[3]
        self.content_height = (height_end - height_start) * self.height_multiplier
        self.update_graph_size()
        self.create_axis()
        self.add_height_clearance_graph()
        self.create_scale()
        self.add_color_scale()

    def create_axis(self):
        bounding_end = abs(self.dimension_analysis.bounding_rect[3])
        bounding_start = abs(self.dimension_analysis.bounding_rect[2])
        pen = QPen()
        pen.setWidthF(0.5)
        # horizontal line
        self.graph_zero[0] = self.position[0] + self.margin - self.line_extend
        self.graph_zero[1] = self.position[1] + bounding_start * self.height_multiplier + self.margin
        self.graph_end[0] = self.graph_zero[0] + self.content_width + self.line_extend
        self.graph_end[1] = self.graph_zero[1]
        line_item_horizontal = QGraphicsLineItem(self.graph_zero[0], self.graph_zero[1], self.graph_end[0], self.graph_end[1])
        line_item_horizontal.setPen(pen)
        self.addToGroup(line_item_horizontal)
        center = (self.graph_zero[0] + self.line_extend), self.graph_zero[1]
        y_top = center[1] - (bounding_start*self.height_multiplier)
        y_bottom = center[1]+(bounding_end*self.height_multiplier)
        line_item_vertical = QGraphicsLineItem(center[0], y_top, center[0], y_bottom)
        line_item_vertical.setPen(pen)
        self.addToGroup(line_item_vertical)

    def create_scale(self):
        section_num = len(self.section_analyzer.section_list)
        section_distance = self.section_analyzer.section_distance
        total_distance = section_num * section_distance
        div = int(Math.integer_division(total_distance, 1.0))
        print(total_distance)
        for i in range(div+1):
            x = self.graph_zero[0] + i * self.length_multiplier + self.line_extend
            y = self.graph_zero[1]
            scale_text = QGraphicsSimpleTextItem("%.2f" % float(i))
            scale_text.setPos(x, y)
            self.addToGroup(scale_text)

    def add_height_clearance_graph(self):
        vertical_clearance = self.clearance_analysis.vertical_clearance
        x_init = self.graph_zero[0] + self.line_extend
        y_init = self.graph_zero[1]
        y_unit_distance = self.clearance_analysis.sampling_distance * self.height_multiplier
        x_unit_distance = self.clearance_analysis.section_distance * self.length_multiplier
        for i in range(len(vertical_clearance)):
            for j in range(len(vertical_clearance[i])):
                vertical_distance = vertical_clearance[i][j]
                if vertical_distance:
                    vertical_distance_value = vertical_distance[0]
                    scene_x = (vertical_distance[1].point.Y() * self.length_multiplier + x_init) - x_unit_distance/2
                    scene_y = (vertical_distance[1].point.X() * self.height_multiplier + y_init) - y_unit_distance/2
                    rect = QGraphicsRectItem(scene_x, scene_y, x_unit_distance, y_unit_distance)
                    color = self.color_interpolation.get_interpolation_from_value(vertical_distance_value)
                    pen = QPen()
                    pen.setStyle(Qt.NoPen)
                    brush = QBrush(color)
                    rect.setPen(pen)
                    rect.setBrush(brush)
                    rect.setZValue(-1.0)
                    self.addToGroup(rect)
                    pass

    def add_color_scale(self):
        x_init = self.graph_zero[0] + self.line_extend
        y_init = self.graph_zero[1] + abs(self.dimension_analysis.bounding_rect[3]) * self.height_multiplier + self.line_extend
        square_size = 10.0
        for i in range(10):
            x = x_init + i * square_size
            y = y_init
            rect = QGraphicsRectItem(x, y, square_size, square_size)
            pen = QPen()
            pen.setWidth(0.01)
            value = (float(i)/9 * (self.vertical_clearance_max - self.vertical_clearance_min)) + self.vertical_clearance_min
            color = self.color_interpolation.get_interpolation_from_value(value)
            brush = QBrush(color)
            rect.setPen(pen)
            rect.setBrush(brush)
            self.addToGroup(rect)
            if i == 0:
                text_start = QGraphicsSimpleTextItem("%.2f" % float(self.vertical_clearance_min))
                text_start.setPos(x, y + square_size)
                self.addToGroup(text_start)
            if i == 9:
                text_end = QGraphicsSimpleTextItem("%.2f" % float(self.vertical_clearance_max))
                text_end.setPos(x, y + square_size)
                self.addToGroup(text_end)


class LeftSurfaceGraph(BaseGraphic):
    def __init__(self, *args):
        super(LeftSurfaceGraph, self).__init__(*args)
        self.dimension_analysis = self.section_analyzer.dimension_analysis
        self.surface_analysis = self.section_analyzer.surface_analysis
        self.surface = self.surface_analysis.left_surface
        self.sampling_distance = self.surface_analysis.sampling_distance
        self.graph_zero = [None, None]
        self.graph_end = [None, None]
        self.rect_list = []
        self.visualization_mode = 0
        self.init_dimension()

    def init_dimension(self):
        super(LeftSurfaceGraph, self).init_dimension()
        self.content_height = len(self.surface[0])* self.sampling_distance * self.height_multiplier
        self.update_graph_size()
        self.create_axis()
        self.create_scale()
        self.add_surface_element()

    def create_axis(self):
        counter = len(self.surface[0]) - 1
        while self.surface[0][counter] is None: # get the first tile
            counter -= 1
        # determining the distance from top elevation
        elevation_coordinate = self.surface[0][counter].point.Z()
        distance_dismissed = len(self.surface[0]) - 1 - counter
        distance = (elevation_coordinate + distance_dismissed * self.sampling_distance) * self.height_multiplier
        pen = QPen()
        pen.setWidthF(0.5)
        self.graph_zero[0] = self.position[0] + self.margin - self.line_extend
        self.graph_zero[1] = self.position[1] + distance + self.margin
        self.graph_end[0] = self.graph_zero[0] + self.content_width + self.line_extend
        self.graph_end[1] = self.graph_zero[1]
        line_item_horizontal = QGraphicsLineItem(self.graph_zero[0], self.graph_zero[1], self.graph_end[0], self.graph_end[1])
        line_item_horizontal.setPen(pen)
        self.addToGroup(line_item_horizontal)
        center = (self.graph_zero[0] + self.line_extend), self.graph_zero[1]
        y_top = center[1] - distance
        y_bottom = self.position[1] + self.margin + len(self.surface[0]) * self.sampling_distance * self.height_multiplier
        line_item_vertical = QGraphicsLineItem(center[0], y_top, center[0], y_bottom)
        line_item_vertical.setPen(pen)
        self.addToGroup(line_item_vertical)

    def create_scale(self):
        section_num = len(self.section_analyzer.section_list)
        section_distance = self.section_analyzer.section_distance
        total_distance = section_num * section_distance
        div = int(Math.integer_division(total_distance, 1.0))
        print(total_distance)
        for i in range(div+1):
            x = self.graph_zero[0] + i * self.length_multiplier + self.line_extend
            y = self.graph_zero[1]
            scale_text = QGraphicsSimpleTextItem("%.2f" % float(i))
            scale_text.setPos(x, y)
            self.addToGroup(scale_text)

    def add_surface_element(self):
        element_wrapper_dict = self.parent.element_name_dict
        x_init = self.graph_zero[0] + self.line_extend
        y_init = self.graph_zero[1] # + self.position[1] + self.margin from bottom of graph
        x_unit_distance = self.surface_analysis.section_distance * self.length_multiplier
        y_unit_distance = self.surface_analysis.sampling_distance * self.height_multiplier
        for i in range(len(self.surface)):
            for j in range(len(self.surface[i])):
                point_object = self.surface[i][j]
                if point_object:
                    element_name = point_object.element.name
                    element_wrapper = element_wrapper_dict.get(element_name)
                    material = point_object.material
                    scene_x = (point_object.point.Y() * self.length_multiplier + x_init) - x_unit_distance/2
                    scene_y = (- point_object.point.Z() * self.length_multiplier) + y_init - y_unit_distance/2
                    rect = QGraphicsRectItem(scene_x, scene_y, x_unit_distance, y_unit_distance)
                    pen = QPen()
                    pen.setStyle(Qt.NoPen)
                    rect.setPen(pen)
                    surface_color = material.get_surface_colour()
                    transparency = material.get_transparency()
                    reflectance = material.get_reflectance()
                    reflectance_method = material.get_reflectance_method()
                    slip_coefficient = material.get_slip_coefficient()
                    imperviousness = material.get_imperviousness()
                    self.rect_list.append((rect, surface_color, transparency, reflectance,reflectance_method, slip_coefficient, imperviousness))
                    self.set_rect_fill(self.visualization_mode, rect, surface_color)
                    rect.setZValue(-1.0)
                    if element_wrapper:
                        element_wrapper.add_graphic_item(rect)
                    self.addToGroup(rect)



class BottomSurfaceGraph(BaseGraphic):
    def __init__(self, *args):
        super(BottomSurfaceGraph, self).__init__(*args)
        self.dimension_analysis = self.section_analyzer.dimension_analysis
        self.surface_analysis = self.section_analyzer.surface_analysis
        self.surface = self.surface_analysis.bottom_surface
        self.sampling_distance = self.surface_analysis.sampling_distance
        self.graph_zero = [None, None]
        self.graph_end = [None, None]
        self.rect_list = []
        self.visualization_mode = 0
        self.init_dimension()

    def init_dimension(self):
        super(BottomSurfaceGraph, self).init_dimension()
        self.content_height = len(self.surface[0]) * self.sampling_distance * self.height_multiplier
        self.update_graph_size()
        self.create_axis()
        self.create_scale()
        self.add_surface_element()

    def create_axis(self):
        counter = 0
        while self.surface[0][counter] is None: #get the first tile
            counter += 1
        # determining the distance from left side
        left_coordinate = abs(self.surface[0][counter].point.X())
        distance = (left_coordinate + counter * self.sampling_distance) * self.height_multiplier
        pen = QPen()
        pen.setWidthF(0.5)
        self.graph_zero[0] = self.position[0] + self.margin - self.line_extend
        self.graph_zero[1] = self.position[1] + distance + self.margin
        self.graph_end[0] = self.graph_zero[0] + self.content_width + self.line_extend
        self.graph_end[1] = self.graph_zero[1]
        line_item_horizontal = QGraphicsLineItem(self.graph_zero[0], self.graph_zero[1], self.graph_end[0], self.graph_end[1])
        line_item_horizontal.setPen(pen)
        self.addToGroup(line_item_horizontal)
        center = (self.graph_zero[0] + self.line_extend), self.graph_zero[1]
        y_top = center[1] - distance
        y_bottom = self.position[1] + self.margin + len(self.surface[0]) * self.sampling_distance * self.height_multiplier
        line_item_vertical = QGraphicsLineItem(center[0], y_top, center[0], y_bottom)
        line_item_vertical.setPen(pen)
        self.addToGroup(line_item_vertical)

    def create_scale(self):
        section_num = len(self.section_analyzer.section_list)
        section_distance = self.section_analyzer.section_distance
        total_distance = section_num * section_distance
        div = int(Math.integer_division(total_distance, 1.0))
        print(total_distance)
        for i in range(div+1):
            x = self.graph_zero[0] + i * self.length_multiplier + self.line_extend
            y = self.graph_zero[1]
            scale_text = QGraphicsSimpleTextItem("%.2f" % float(i))
            scale_text.setPos(x, y)
            self.addToGroup(scale_text)

    def add_surface_element(self):
        element_wrapper_dict = self.parent.element_name_dict
        x_init = self.graph_zero[0] + self.line_extend
        y_init = self.graph_zero[1]
        y_unit_distance = self.surface_analysis.sampling_distance * self.height_multiplier
        x_unit_distance = self.surface_analysis.section_distance * self.length_multiplier
        for i in range(len(self.surface)):
            for j in range(len(self.surface[i])):
                point_object = self.surface[i][j]
                if point_object:
                    element_name = point_object.element.name
                    element_wrapper = element_wrapper_dict.get(element_name)
                    material = point_object.material
                    scene_x = point_object.point.Y() * self.length_multiplier + x_init - x_unit_distance/2
                    scene_y = point_object.point.X() * self.height_multiplier + y_init - y_unit_distance/2
                    rect = QGraphicsRectItem(scene_x, scene_y, x_unit_distance, y_unit_distance)
                    pen = QPen()
                    pen.setStyle(Qt.NoPen)
                    rect.setPen(pen)
                    surface_color = material.get_surface_colour()
                    transparency = material.get_transparency()
                    reflectance = material.get_reflectance()
                    reflectance_method = material.get_reflectance_method()
                    slip_coefficient = material.get_slip_coefficient()
                    imperviousness = material.get_imperviousness()
                    self.rect_list.append((rect, surface_color, transparency, reflectance,reflectance_method, slip_coefficient, imperviousness))
                    self.set_rect_fill(self.visualization_mode, rect, surface_color)
                    rect.setZValue(-1.0)
                    if element_wrapper:
                        element_wrapper.add_graphic_item(rect)
                    self.addToGroup(rect)


class RightSurfaceGraph(BaseGraphic):
    def __init__(self, *args):
        super(RightSurfaceGraph, self).__init__(*args)
        self.dimension_analysis = self.section_analyzer.dimension_analysis
        self.surface_analysis = self.section_analyzer.surface_analysis
        self.surface = self.surface_analysis.right_surface
        self.sampling_distance = self.surface_analysis.sampling_distance
        self.graph_zero = [None, None]
        self.graph_end = [None, None]
        self.rect_list = []
        self.visualization_mode = 0
        self.init_dimension()

    def init_dimension(self):
        super(RightSurfaceGraph, self).init_dimension()
        self.content_height = len(self.surface[0]) * self.sampling_distance * self.height_multiplier
        self.update_graph_size()
        self.create_axis()
        self.create_scale()
        self.add_surface_element()

    def create_axis(self):
        counter = 0
        while self.surface[0][counter] is None: #get the first tile from bottom
            counter += 1
        # determining the distance from lower elevation
        elevation_coordinate = -(self.surface[0][counter].point.Z())
        distance = (counter * self.sampling_distance + elevation_coordinate)* self.height_multiplier
        pen = QPen()
        pen.setWidthF(0.5)
        self.graph_zero[0] = self.position[0] + self.margin - self.line_extend
        self.graph_zero[1] = self.position[1] + distance + self.margin
        self.graph_end[0] = self.graph_zero[0] + self.content_width + self.line_extend
        self.graph_end[1] = self.graph_zero[1]
        line_item_horizontal = QGraphicsLineItem(self.graph_zero[0], self.graph_zero[1], self.graph_end[0], self.graph_end[1])
        line_item_horizontal.setPen(pen)
        self.addToGroup(line_item_horizontal)
        center = (self.graph_zero[0] + self.line_extend), self.graph_zero[1]
        y_top = center[1] - distance
        y_bottom = self.position[1] + self.margin + len(self.surface[0]) * self.sampling_distance * self.height_multiplier
        line_item_vertical = QGraphicsLineItem(center[0], y_top, center[0], y_bottom)
        line_item_vertical.setPen(pen)
        self.addToGroup(line_item_vertical)

    def create_scale(self):
        section_num = len(self.section_analyzer.section_list)
        section_distance = self.section_analyzer.section_distance
        total_distance = section_num * section_distance
        div = int(Math.integer_division(total_distance, 1.0))
        print(total_distance)
        for i in range(div+1):
            x = self.graph_zero[0] + i * self.length_multiplier + self.line_extend
            y = self.graph_zero[1]
            scale_text = QGraphicsSimpleTextItem("%.2f" % float(i))
            scale_text.setPos(x, y)
            self.addToGroup(scale_text)

    def add_surface_element(self):
        element_wrapper_dict = self.parent.element_name_dict
        x_init = self.graph_zero[0] + self.line_extend
        y_init = self.graph_zero[1]
        x_unit_distance = self.surface_analysis.section_distance * self.length_multiplier
        y_unit_distance = self.surface_analysis.sampling_distance * self.height_multiplier
        for i in range(len(self.surface)):
            for j in range(len(self.surface[i])):
                point_object = self.surface[i][j]
                if point_object:
                    element_name = point_object.element.name
                    element_wrapper = element_wrapper_dict.get(element_name)
                    material = point_object.material
                    scene_x = (point_object.point.Y() * self.length_multiplier + x_init) - x_unit_distance/2
                    scene_y = (point_object.point.Z() * self.length_multiplier + y_init) - y_unit_distance/2
                    rect = QGraphicsRectItem(scene_x, scene_y, x_unit_distance, y_unit_distance)
                    pen = QPen()
                    pen.setStyle(Qt.NoPen)
                    rect.setPen(pen)
                    surface_color = material.get_surface_colour()
                    transparency = material.get_transparency()
                    reflectance = material.get_reflectance()
                    reflectance_method = material.get_reflectance_method()
                    slip_coefficient = material.get_slip_coefficient()
                    imperviousness = material.get_imperviousness()
                    self.rect_list.append((rect, surface_color, transparency, reflectance,reflectance_method, slip_coefficient, imperviousness))
                    self.set_rect_fill(self.visualization_mode, rect, surface_color)
                    rect.setZValue(-1.0)
                    if element_wrapper:
                        element_wrapper.add_graphic_item(rect)
                    self.addToGroup(rect)

class UpperSurfaceGraph(BaseGraphic):
    def __init__(self, *args):
        super(UpperSurfaceGraph, self).__init__(*args)
        self.dimension_analysis = self.section_analyzer.dimension_analysis
        self.surface_analysis = self.section_analyzer.surface_analysis
        self.surface = self.surface_analysis.upper_surface
        self.sampling_distance = self.surface_analysis.sampling_distance
        self.graph_zero = [None, None]
        self.graph_end = [None, None]
        self.rect_list = []
        self.visualization_mode = 0
        self.init_dimension()

    def init_dimension(self):
        super(UpperSurfaceGraph, self).init_dimension()
        self.content_height = len(self.surface[0]) * self.sampling_distance * self.height_multiplier
        self.update_graph_size()
        self.create_axis()
        self.create_scale()
        self.add_surface_element()

    def create_axis(self):
        counter = 0
        while self.surface[0][counter] is None: #get the first tile
            counter += 1
        # determining the distance from left side
        left_coordinate = abs(self.surface[0][counter].point.X())
        distance = (left_coordinate + counter * self.sampling_distance) * self.height_multiplier
        pen = QPen()
        pen.setWidthF(0.5)
        self.graph_zero[0] = self.position[0] + self.margin - self.line_extend
        self.graph_zero[1] = self.position[1] + distance + self.margin
        self.graph_end[0] = self.graph_zero[0] + self.content_width + self.line_extend
        self.graph_end[1] = self.graph_zero[1]
        line_item_horizontal = QGraphicsLineItem(self.graph_zero[0], self.graph_zero[1], self.graph_end[0], self.graph_end[1])
        line_item_horizontal.setPen(pen)
        self.addToGroup(line_item_horizontal)
        center = (self.graph_zero[0] + self.line_extend), self.graph_zero[1]
        y_top = center[1] - distance
        y_bottom = self.position[1] + self.margin + len(self.surface[0]) * self.sampling_distance * self.height_multiplier
        line_item_vertical = QGraphicsLineItem(center[0], y_top, center[0], y_bottom)
        line_item_vertical.setPen(pen)
        self.addToGroup(line_item_vertical)

    def create_scale(self):
        section_num = len(self.section_analyzer.section_list)
        section_distance = self.section_analyzer.section_distance
        total_distance = section_num * section_distance
        div = int(Math.integer_division(total_distance, 1.0))
        print(total_distance)
        for i in range(div+1):
            x = self.graph_zero[0] + i * self.length_multiplier + self.line_extend
            y = self.graph_zero[1]
            scale_text = QGraphicsSimpleTextItem("%.2f" % float(i))
            scale_text.setPos(x, y)
            self.addToGroup(scale_text)

    def add_surface_element(self):
        element_wrapper_dict = self.parent.element_name_dict
        x_init = self.graph_zero[0] + self.line_extend
        y_init = self.graph_zero[1]
        y_unit_distance = self.surface_analysis.sampling_distance * self.height_multiplier
        x_unit_distance = self.surface_analysis.section_distance * self.length_multiplier
        for i in range(len(self.surface)):
            for j in range(len(self.surface[i])):
                point_object = self.surface[i][j]
                if point_object:
                    element_name = point_object.element.name
                    element_wrapper = element_wrapper_dict.get(element_name)
                    material = point_object.material
                    scene_x = point_object.point.Y() * self.length_multiplier + x_init - x_unit_distance/2
                    scene_y = point_object.point.X() * self.height_multiplier + y_init - y_unit_distance/2
                    rect = QGraphicsRectItem(scene_x, scene_y, x_unit_distance, y_unit_distance)
                    pen = QPen()
                    pen.setStyle(Qt.NoPen)
                    rect.setPen(pen)
                    surface_color = material.get_surface_colour()
                    transparency = material.get_transparency()
                    reflectance = material.get_reflectance()
                    reflectance_method = material.get_reflectance_method()
                    slip_coefficient = material.get_slip_coefficient()
                    imperviousness = material.get_imperviousness()
                    self.rect_list.append((rect, surface_color, transparency, reflectance,reflectance_method, slip_coefficient, imperviousness))
                    self.set_rect_fill(self.visualization_mode, rect, surface_color)
                    rect.setZValue(-1.0)
                    if element_wrapper:
                        element_wrapper.add_graphic_item(rect)
                    self.addToGroup(rect)





