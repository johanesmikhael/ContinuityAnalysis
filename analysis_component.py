
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsItemGroup, QGraphicsLineItem, QGraphicsSimpleTextItem
from PyQt5.QtCore import qAbs, QLineF, QPointF, qrand, QRectF, QSizeF, qsrand, Qt, QTime
from PyQt5.QtGui import QPen
from util import Math

class BaseGraphic(QGraphicsItemGroup):
    def __init__(self, *args):
        super(BaseGraphic, self).__init__()
        self.label = args[3]
        self.parent = args[0]
        self.section_analyzer = self.parent.section_analyzer
        self.width = None
        self.height = None
        self.margin = None
        self.position = None
        self.content_width = None
        self.content_height = None
        self.section_num = len(self.section_analyzer.section_list)
        self.section_distance = self.section_analyzer.section_distance
        self.length_multiplier = 100.0
        self.height_multiplier = 100.0
        self.line_extend = 10
        self.margin = 30

    def init_dimension(self):
        section_num = len(self.section_analyzer.section_list)
        section_distance = self.section_analyzer.section_distance
        self.content_width = section_num * section_distance * self.length_multiplier

    def update_graph_size(self):
        if self.content_height and self.content_width:
            self.width = self.content_width + self.margin * 2
            self.height = self.content_height + self.margin *2
        bounding_rect = self.boundingRect()
        # bounding_rect.setWidth(self.width)
        # bounding_rect.setHeight(self.height)


class ClearanceWidthGraph(BaseGraphic):
    def __init__(self, *args):
        super(ClearanceWidthGraph, self).__init__(*args)
        self.position = args[1], args[2]
        self.dimension_analysis = self.section_analyzer.dimension_analysis
        self.clearance_analysis = self.section_analyzer.clearance_analysis
        self.graph_zero = [None, None]
        self.graph_end = [None, None]
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
        height_end = self.dimension_analysis.bounding_rect[1]
        pen = QPen()
        pen.setWidthF(0.5)
        # horizontal line
        self.graph_zero[0] = self.position[0] + self.margin - self.line_extend
        self.graph_zero[1] = self.position[0] + height_end * self.height_multiplier + self.margin
        self.graph_end[0] = self.graph_zero[0] + self.content_width + self.line_extend
        self.graph_end[1] = y_end = self.graph_zero[1]
        line_item_horizontal = QGraphicsLineItem(self.graph_zero[0], self.graph_zero[1], self.graph_end[0], self.graph_end[1])
        line_item_horizontal.setPen(pen)
        self.addToGroup(line_item_horizontal)
        center = (self.graph_zero[0] + self.line_extend), self.graph_zero[1]
        y_top = center[1] - (height_end/2*self.height_multiplier)
        y_bottom = center[1]+(height_end/2*self.height_multiplier)
        line_item_vertical = QGraphicsLineItem(center[0], y_top, center[0], y_bottom)
        line_item_vertical.setPen(pen)
        self.addToGroup(line_item_vertical)

    def create_scale(self):
        section_num = len(self.section_analyzer.section_list)
        section_distance = self.section_analyzer.section_distance
        total_distance = section_num * section_distance
        div = int(Math.integer_division(total_distance, 1.0))
        print total_distance
        for i in range(div+1):
            x = self.graph_zero[0] + i * self.length_multiplier + self.line_extend
            y = self.graph_zero[1]
            scale_text = QGraphicsSimpleTextItem("%.2f" % float(i))
            scale_text.setPos(x, y)
            self.addToGroup(scale_text)

    def add_clearance_graph(self):
        print"-----------------------------------------"
        horizontal_clearance = self.clearance_analysis.horizontal_clearance
        x_init = self.graph_zero[0] + self.line_extend
        y_init = self.graph_zero[1]
        for i in range(len(horizontal_clearance)):
            clearance_points = horizontal_clearance[i]
            x = x_init + i * self.dimension_analysis.section_distance * self.length_multiplier
            y_top = y_init + clearance_points[0] * self.height_multiplier
            y_bottom = y_init + clearance_points[1] * self.height_multiplier
            pen = QPen()
            pen.setColor()
            line = QGraphicsLineItem(x, y_top, x, y_bottom)
            self.addToGroup(line)
        pass

