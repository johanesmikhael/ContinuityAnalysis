from slice_analyzer import *
from util import Color
from slice_visualization_ui import Ui_slice_visualization_gui
from PyQt5 import QtGui, QtCore, QtWidgets
from analysis_visualization_gui import GuiAnalysisVisualization
from slice_visualization_widget import SliceVisualizationWidget
from tkinter import Tk
import tkinter.filedialog
from os.path import isfile


class GuiVisualization(QtWidgets.QMainWindow):
    def __init__(self, *args):
        self.parent = args[0]
        QtWidgets.QMainWindow.__init__(self)
        # self.ui = Ui_slice_visualization()
        self.ui = Ui_slice_visualization_gui()
        self.ui.setupUi(self)
        self.setWindowTitle("Slice Visualization")
        self.resize(2048, 1200)
        self.canvas = SliceVisualizationWidget(self)
        # self.ui.horizontalLayout_main.addWidget(self.canvas)
        self.setCentralWidget(self.canvas)
        self._toolbars = {}
        self._toolbar_methods = {}
        self.setup_toolbar()
        self.slice_analyzer = SliceAnalyzer()
        self.slice_axis = None
        self.viewer_bg_color = Color.white
        self.is_show_slice = True
        self.analysis_visualization_win = None

    def add_toolbar(self, toolbar_name):
        # _toolbar = QtWidgets.QToolBar(toolbar_name)
        # self.ui.verticalLayout_toolbar.addWidget(_toolbar)
        _toolbar = self.addToolBar(toolbar_name)
        self._toolbars[toolbar_name] = _toolbar
        pass

    def add_function_to_toolbar(self, toolbar_name, _callable):
        assert callable(_callable), "the function supplied is not callable"
        try:
            _action = QtWidgets.QAction(_callable.__name__.replace('_', ' ').lower(), self)
            # self.connect(_action, QtCore.pyqtSignal('triggered()'), _callable)
            _action.triggered.connect(_callable)
            self._toolbars[toolbar_name].addSeparator()
            self._toolbars[toolbar_name].addAction(_action)
        except KeyError:
            raise ValueError("the %s toolbar does not exist" % toolbar_name)

    def setup_toolbar(self):
        self.add_toolbar("Main Toolbar")
        self.addToolBarBreak()
        self.add_toolbar("View Toolbar")
        self.addToolBarBreak()
        self.add_toolbar("Slice Analysis Toolbar")
        self.addToolBarBreak()
        self.add_toolbar("Slice_Graph_Toolbar")
        self.add_function_to_toolbar("Main Toolbar", self.export_image)
        self.add_function_to_toolbar("View Toolbar", self.toggle_slice_view)
        self.add_function_to_toolbar("View Toolbar", self.top_view)
        self.add_function_to_toolbar("View Toolbar", self.iso_view)
        self.add_function_to_toolbar("Slice Analysis Toolbar", self.analyze_slice)
        self.add_function_to_toolbar("Slice Analysis Toolbar", self.toggle_left_surface_view)
        self.add_function_to_toolbar("Slice Analysis Toolbar", self.toggle_right_surface_view)
        self.add_function_to_toolbar("Slice Analysis Toolbar", self.toggle_floor_surface_view)
        self.add_function_to_toolbar("Slice Analysis Toolbar", self.toggle_ceiling_surface_view)
        self.add_function_to_toolbar("Slice Analysis Toolbar", self.toggle_feature_view)
        self.add_function_to_toolbar("Slice_Graph_Toolbar", self.create_graph)
        self.add_function_to_toolbar("Slice_Graph_Toolbar", self.save_graph)
        self.add_function_to_toolbar("Slice_Graph_Toolbar", self.calculate_kernel)
        self.add_function_to_toolbar("Slice_Graph_Toolbar", self.generate_som)
        self.add_function_to_toolbar("Slice_Graph_Toolbar", self.toggle_path_annotation_view)

    def export_image(self):
        f = self.canvas.get_display().View.View().GetObject()
        # print f.Export("tetesdrf.svg", Graphic3d_EF_SVG)
        import datetime
        now = datetime.datetime.now()
        now_str = now.strftime("%Y-%m-%d_%H%M%S")
        print(self.canvas.get_display().View.Dump(now_str+"_export_slices.png"))
        pass

    def create_graph(self):
        self.slice_analyzer.create_graph()

    def save_graph(self):
        self.slice_analyzer.save_graph()

    def calculate_kernel(self):
        self.slice_analyzer.calculate_kernel()

    def generate_som(self):
        self.slice_analyzer.generate_som()

    def toggle_path_annotation_view(self):
        self.slice_analyzer.toggle_path_annotation_view()

    def get_init_slice(self):
        self.slice_analyzer.init(self)
        self.canvas.get_display().FitAll()

    def analyze_slice(self):
        self.slice_analyzer.analyze_slice()

    def toggle_left_surface_view(self):
        self.slice_analyzer.toggle_left_surface_view()

    def toggle_right_surface_view(self):
        self.slice_analyzer.toggle_right_surface_view()

    def toggle_floor_surface_view(self):
        self.slice_analyzer.toggle_floor_surface_view()

    def toggle_ceiling_surface_view(self):
        self.slice_analyzer.toggle_ceiling_surface_view()

    def toggle_feature_view(self):
        self.slice_analyzer.toggle_feature_surface_view()

    def toggle_slice_view(self):
        self.is_show_slice = not self.is_show_slice
        self.slice_analyzer.show_slice_surface(self.is_show_slice)

    def top_view(self):
        display = self.canvas.get_display()
        display.View_Top()
        display.FitAll()
        display.ZoomFactor(0.9)
        pass

    def iso_view(self):
        display = self.canvas.get_display()
        display.View_Iso()
        display.FitAll()
        display.ZoomFactor(0.9)
