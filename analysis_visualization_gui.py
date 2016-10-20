from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsLineItem
from PyQt5.QtGui import QPainter
from analysis_visualization_ui import Ui_analysis_visualization_gui
from analysis_component import *


class GuiAnalysisVisualization(QtWidgets.QMainWindow):
    def __init__(self, *args):
        self.parent = args[0]
        self.section_analyzer = self.parent.section_analyzer
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_analysis_visualization_gui()
        self.ui.setupUi(self)
        self.setWindowTitle("Analysis Visualization")
        self.resize(1024, 600)
        self._toolbars = {}
        self._toolbar_methods = {}
        self.setup_toolbar()
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 600, 1000)
        self.ui.graphicsView.setScene(self.scene)
        self.ui.graphicsView.setRenderHint(QPainter.Antialiasing)
        self.graphics = []

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

    def add_clearance_width_graph(self):
        y_pos = self.get_y_pos()
        x_pos = 0
        clearance_width_graph = ClearanceWidthGraph(self, x_pos, y_pos, "dimension width")
        self.scene.addItem(clearance_width_graph)

    def get_y_pos(self):
        y_init = 0
        for graphic in self.graphics:
            y_init += graphic.height
        return y_init

