from section_analyzer import *
from quantity import Color

class GuiVisualization(QtGui.QWidget):
    def __init__(self, *args):
        self.parent = args[0]
        QtGui.QWidget.__init__(self)
        self.ui = Ui_section_visualization()
        self.ui.setupUi(self)
        self.setWindowTitle("Section Visualization")
        self.canvas = SectionVisualizationWidget(self)
        self.ui.verticalLayout.addWidget(self.canvas)
        self._toolbars = {}
        self._toolbar_methods = {}
        self.setup_toolbar()
        self.section_analyzer = SectionAnalyzer()
        self.section_axis = None
        self.viewer_bg_color = Color.white
        self.show_section = True

    def add_toolbar(self, toolbar_name):
        _toolbar = QtGui.QToolBar(toolbar_name)
        self.ui.verticalLayout_toolbar.addWidget(_toolbar)
        self._toolbars[toolbar_name] = _toolbar
        pass

    def add_function_to_toolbar(self, toolbar_name, _callable):
        assert callable(_callable), "the function supplied is not callable"
        try:
            _action = QtGui.QAction(_callable.__name__.replace('_', ' ').lower(), self)
            self.connect(_action, QtCore.SIGNAL('triggered()'), _callable)
            self._toolbars[toolbar_name].addSeparator()
            self._toolbars[toolbar_name].addAction(_action)
        except KeyError:
            raise ValueError("the %s toolbar does not exist" % toolbar_name)

    def setup_toolbar(self):
        self.add_toolbar("Main Toolbar")
        self.add_function_to_toolbar("Main Toolbar", self.export_svg)
        self.add_function_to_toolbar("Main Toolbar", self.analyze)
        self.add_function_to_toolbar("Main Toolbar", self.toggle_section_view)
        pass

    def export_svg(self):
        f = self.canvas.get_display().View.View().GetObject()
        print f.Export("tetesdrf.svg", Graphic3d_EF_SVG)
        pass

    def get_init_section(self):
        self.section_analyzer.init(self)
        self.canvas.get_display().FitAll()

    def analyze(self):
        self.section_analyzer.analyze_dimension()
        pass

    def toggle_section_view(self):
        self.show_section = not self.show_section
        self.section_analyzer.show_section_wire(self.show_section)


