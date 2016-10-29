from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsLineItem
from PyQt5.QtWidgets import QListWidgetItem, QFileDialog
from PyQt5.QtGui import QPainter, QImage, QPixmap
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtCore import QFileInfo
from PyQt5.QtCore import QFileInfo
from analysis_visualization_ui import Ui_analysis_visualization_gui
from analysis_component import *
from analysis_graphic_view_widget import AnalysisViewWidget
from tkinter import Tk
import tkinter.filedialog

class GuiAnalysisVisualization(QtWidgets.QMainWindow):
    def __init__(self, *args):
        self.parent = args[0]
        self.main_gui = self.parent.parent
        self.section_analyzer = self.parent.section_analyzer
        self.elements = self.main_gui.elements
        QtWidgets.QMainWindow.__init__(self)
        self.section_distance = self.section_analyzer.section_distance
        self.section_num = len(self.section_analyzer.section_list)
        self.max_distance = self.section_distance * self.section_num
        self.current_distance = 0
        self.ui = Ui_analysis_visualization_gui()
        self.ui.setupUi(self)
        self.setWindowTitle("Analysis Visualization")
        self.resize(1024, 600)
        self._toolbars = {}
        self._toolbar_methods = {}
        self.setup_toolbar()
        self.graphic_view = None
        self.scene = None
        self.element_name_dict = {}
        self.element_list_item_dict = {}
        self.current_selection_item = []
        self.initUI()
        # self.ui.graphicsView.setScene(self.scene)
        # self.ui.graphicsView.setRenderHint(QPainter.Antialiasing)
        self.graphics = []

    def initUI(self):
        self.set_distance_slider()
        self.graphic_view = AnalysisViewWidget(self)
        self.scene = QGraphicsScene()
        self.graphic_view.setScene(self.scene)
        self.ui.verticalLayout.addWidget(self.graphic_view)
        self.ui.verticalSlider_distance.valueChanged.connect(self.set_distance_value)
        self.ui.listWidget_elements.itemSelectionChanged.connect(self.set_element_selection)
        self.set_element_list()
        self.add_dummy_line()

    def set_element_selection(self):
        selection = self.ui.listWidget_elements.selectedItems()
        selection_dict = {}
        for item in selection:
            selection_dict[item.text()] = item
        if not self.current_selection_item:
            self.current_selection_item = selection_dict
            for key, item, in self.current_selection_item.items():
                element = item.data(Qt.UserRole + 2)
                element.set_selected(True)
        else:
            # check new selected item:
            for key, item in selection_dict.items():
                if not(key in self.current_selection_item):
                    self.current_selection_item[key] = item
                    element = item.data(Qt.UserRole + 2)
                    element.set_selected(True)
            # check for new unselected item:
            key_to_remove = []
            for key, item in self.current_selection_item.items():
                if not(key in selection_dict):
                    element = item.data(Qt.UserRole + 2)
                    element.set_selected(False)
                    key_to_remove.append(key)
            for key in key_to_remove:
                del self.current_selection_item[key]
        print(len(selection))
        print(len(self.current_selection_item))

    def set_element_list(self):
        self.ui.listWidget_elements.clear()
        for element in self.elements:
            element_name = element.name
            if not (element_name in self.element_name_dict):  # no element to that name yet
                element_wrapper = GraphicElementsWrapper(element)
                self.element_name_dict[element_name] = element_wrapper
                item = QListWidgetItem()
                item.setText(element_name)
                item.setData(Qt.UserRole + 2, element_wrapper)
                self.element_list_item_dict[element_name] = item
                self.ui.listWidget_elements.addItem(item)
        self.ui.listWidget_elements.sortItems(Qt.AscendingOrder)

    def add_dummy_line(self):
        pen = QPen()
        pen.setStyle(Qt.NoPen)
        dummy_line = QGraphicsLineItem(0, 0, 0, 100)
        dummy_line.setPen(pen)
        self.scene.addItem(dummy_line)

    def set_distance_slider(self):
        slider = self.ui.verticalSlider_distance
        text_label = self.ui.label_distance
        slider.setValue(self.current_distance)
        text_label.setText("%.2f" % self.current_distance)

    def set_distance_value(self):
        slider = self.ui.verticalSlider_distance
        text_label = self.ui.label_distance
        value = slider.value()
        self.current_distance = float(value) / slider.maximum() * self.max_distance
        text_label.setText("%.2f" % self.current_distance)
        self.set_graph_component()
        self.main_gui.set_distance_pointer(self.current_distance)
        pass

    def setSceneSize(self):
        pass

    def setScene(self):
        self.scene = QGraphicsScene()
        # self.scene.setSceneRect(0, 0, 600, 1000)
        pass

    def add_toolbar(self, toolbar_name):
        _toolbar = self.addToolBar(toolbar_name)
        self._toolbars[toolbar_name] = _toolbar

    def add_fuction_to_toolbar(self, toolbar_name, _callable):
        assert callable(_callable), "the function supplied is not callable"
        try:
            _action = QtWidgets.QAction(_callable.__name__.replace('_', ' ').lower(), self)
            _action.triggered.connect(_callable)
            self._toolbars[toolbar_name].addSeparator()
            self._toolbars[toolbar_name].addAction(_action)
        except KeyError:
            raise ValueError("the value %s toolbar does not exist" % toolbar_name)

    def setup_toolbar(self):
        self.add_toolbar("Main Toolbar")
        self.add_fuction_to_toolbar("Main Toolbar", self.add_clearance_width_graph)
        self.add_fuction_to_toolbar("Main Toolbar", self.add_clearance_height_graph)
        self.add_fuction_to_toolbar("Main Toolbar", self.add_surface_graph)
        self.add_fuction_to_toolbar("Main Toolbar", self.export_image)

    def export_image(self):
        # print f.Export("tetesdrf.svg", Graphic3d_EF_SVG)
        '''root = Tk()
        root.withdraw()
        file_name = tkinter.filedialog.asksaveasfile(filetypes=[("PNG files", "*.png")])
        name = str(file_name)+".png"
        root.destroy()'''
        self.scene.setSceneRect(self.scene.itemsBoundingRect())
        image = QImage(self.scene.sceneRect().size().toSize(), QImage.Format_RGB32)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        self.scene.render(painter)
        print(image.save("0002_export_analysis.png"))



    def add_clearance_width_graph(self):
        y_pos = self.get_y_pos()
        x_pos = 0
        clearance_width_graph = ClearanceWidthGraph(self, x_pos, y_pos, "dimension width")
        self.graphics.append(clearance_width_graph)
        # self.scene.addItem(clearance_width_graph)
        for item in clearance_width_graph.items:
            self.scene.addItem(item)
        print("clearance_weight_graph_added")

    def add_clearance_height_graph(self):
        y_pos = self.get_y_pos()
        x_pos = 0
        clearance_height_graph = ClearanceHeightGraph(self, x_pos, y_pos, "dimension height")
        self.graphics.append(clearance_height_graph)
        # self.scene.addItem(clearance_height_graph)
        for item in clearance_height_graph.items:
            self.scene.addItem(item)
        print("clearance_height_graph_added")
        pass

    def add_surface_graph(self):
        y_pos = self.get_y_pos()
        x_pos = 0
        left_surface_graph = LeftSurfaceGraph(self, x_pos, y_pos, "left_surface_graph")
        self.graphics.append(left_surface_graph)
        # self.scene.addItem(left_surface_graph)
        for item in left_surface_graph.items:
            self.scene.addItem(item)
        print("left_sufrace_graph_added")
        y_pos = self.get_y_pos()
        bottom_surface_graph = BottomSurfaceGraph(self, x_pos, y_pos, "bottom_surface_graph")
        self.graphics.append(bottom_surface_graph)
        # self.scene.addItem(bottom_surface_graph)
        for item in bottom_surface_graph.items:
            self.scene.addItem(item)
        print("bottom_surface_graph_added")
        y_pos = self.get_y_pos()
        right_surface_graph = RightSurfaceGraph(self, x_pos, y_pos, "right_surface_graph")
        self.graphics.append(right_surface_graph)
        # self.scene.addItem(right_surface_graph)
        for item in right_surface_graph.items:
            self.scene.addItem(item)
        y_pos = self.get_y_pos()
        upper_surface_graph = UpperSurfaceGraph(self, x_pos, y_pos, "upper_surface_graph")
        self.graphics.append(upper_surface_graph)
        # self.scene.addItem(upper_surface_graph)
        for item in upper_surface_graph.items:
            self.scene.addItem(item)
        self.purge_element_list()
        self.add_dummy_line_for_margin()

    def add_dummy_line_for_margin(self):
        height = self.scene.height()
        width = self.scene.width()
        pen = QPen()
        pen.setStyle(Qt.NoPen)
        dummy_line_a= QGraphicsLineItem(0, height, 0, height + 100)
        dummy_line_b = QGraphicsLineItem(width, 0, width + 100, 0)
        dummy_line_a.setPen(pen)
        dummy_line_b.setPen(pen)
        self.scene.addItem(dummy_line_a)
        self.scene.addItem(dummy_line_b)

    def purge_element_list(self):
        element_list_widget = self.ui.listWidget_elements
        for i in range(element_list_widget.count()):
            item = element_list_widget.item(i)
            element_wrapper = item.data(Qt.UserRole + 2)
            if not element_wrapper.is_analyzed:
                item.setHidden(True)

    def get_y_pos(self):
        y_init = 100
        for graphic in self.graphics:
            y_init += graphic.height
        print(y_init)
        return y_init

    def set_graph_component(self):
        for graph in self.graphics:
            graph.set_distance_pointer(self.current_distance)
        pass


class GraphicElementsWrapper(object):
    def __init__(self, *args):
        self.element = args[0]
        self.name = self.element.name
        self.graphic_item_list = []
        self.is_selected = False
        self.is_analyzed = False
        self.material_dict = {}
        self.material_legends = []

    def add_material_legend(self, material_legend):
        self.material_legends.append(material_legend)

    def add_graphic_item(self, graphic_item, material):
        self.graphic_item_list.append(graphic_item)
        if material.name:
            if not(material.name in self.material_dict):
                self.material_dict[material.name] = material

    def set_selected(self, is_selected):
        if is_selected:
            if not self.is_selected:
                self.is_selected = is_selected
                pen = QPen()
                pen.setWidthF(0.5)
                pen.setColor(Color.create_qcolor_from_rgb_tuple_f((1.0, 0.0, 0.0)))
                for rect in self.graphic_item_list:
                    rect.setPen(pen)
        else:
            if self.is_selected:
                self.is_selected = is_selected
                pen = QPen()
                pen.setStyle(Qt.NoPen)
                for rect in self.graphic_item_list:
                    rect.setPen(pen)



