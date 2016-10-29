from section_analyzer import *
from util import Color
from section_visualization_ui import Ui_section_visualization_gui
from PyQt5 import QtGui, QtCore, QtWidgets
from analysis_visualization_gui import GuiAnalysisVisualization
from section_visualization_widget import SectionVisualizationWidget
from tkinter import Tk
import tkinter.filedialog
from os.path import isfile

class GuiVisualization(QtWidgets.QMainWindow):
    def __init__(self, *args):
        self.parent = args[0]
        QtWidgets.QMainWindow.__init__(self)
        # self.ui = Ui_section_visualization()
        self.ui = Ui_section_visualization_gui()
        self.ui.setupUi(self)
        self.setWindowTitle("Section Visualization")
        self.resize(1024, 600)
        self.canvas = SectionVisualizationWidget(self)
        # self.ui.horizontalLayout_main.addWidget(self.canvas)
        self.setCentralWidget(self.canvas)
        self._toolbars = {}
        self._toolbar_methods = {}
        self.setup_toolbar()
        self.section_analyzer = SectionAnalyzer()
        self.section_axis = None
        self.viewer_bg_color = Color.white
        self.is_show_section = True
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
        self.add_toolbar("View Toolbar")
        self.add_function_to_toolbar("Main Toolbar", self.export_image)
        self.add_function_to_toolbar("Main Toolbar", self.analyze_dimension)
        self.add_function_to_toolbar("Main Toolbar", self.analyze_surface)
        self.add_function_to_toolbar("Main Toolbar", self.analyze_clearance)
        self.add_function_to_toolbar("Main Toolbar", self.analysis_visualization)
        self.add_function_to_toolbar("View Toolbar", self.toggle_section_view)
        self.add_function_to_toolbar("View Toolbar", self.top_view)
        self.add_function_to_toolbar("View Toolbar", self.iso_view)
        pass

    def export_image(self):
        f = self.canvas.get_display().View.View().GetObject()
        # print f.Export("tetesdrf.svg", Graphic3d_EF_SVG)
        print(self.canvas.get_display().View.Dump("0001_export_slices.png"))
        pass

    def get_init_section(self):
        self.section_analyzer.init(self)
        self.canvas.get_display().FitAll()

    def analyze_dimension(self):
        self.section_analyzer.analyze_dimension()
        pass

    def analyze_surface(self):
        self.section_analyzer.analyze_surface()

    def analyze_clearance(self):
        self.section_analyzer.analyze_clearance()

    def toggle_section_view(self):
        self.is_show_section = not self.is_show_section
        self.section_analyzer.show_section_wire(self.is_show_section)

    def analysis_visualization(self):
        if not self.analysis_visualization_win:
            self.analysis_visualization_win = GuiAnalysisVisualization(self)
        if self.analysis_visualization_win.isVisible():
            self.analysis_visualization_win.hide()
        else:
            self.analysis_visualization_win.show()

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


