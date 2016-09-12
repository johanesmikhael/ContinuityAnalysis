from section_analyzer import *

class GuiVisualization(QtGui.QWidget):
    def __init__(self, *args):
        self.parent = args[0]
        QtGui.QWidget.__init__(self)
        self.ui = Ui_section_visualization()
        self.ui.setupUi(self)
        self.setWindowTitle("Section Visualization")
        self.canvas = SectionVisualizationWidget()
        self.ui.verticalLayout.addWidget(self.canvas)
        self._toolbars = {}
        self._toolbar_methods = {}
        self.setup_toolbar()
        self.section_analyzer = SectionAnalyzer()
        self.section_axis = None

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
        pass

    def export_svg(self):
        f = self.canvas.get_display().View.View().GetObject()
        print f.Export("tetesdrf.svg", Graphic3d_EF_SVG)
        pass

    def get_init_section(self):
        self.section_analyzer.init(self)
        self.canvas.get_display().FitAll()

    def analyze(self):
        self.analyze_dimension()
        pass

    def analyze_dimension(self):
        for i, section in enumerate(self.section_list):
            x = i * self.parent.section_distance
            origin_point = gp_Pnt(x, 0.0, 1.0)
            bottom_point = gp_Pnt(x, 0.0, -4.0)
            section_edge = BRepBuilderAPI_MakeEdge(origin_point, bottom_point).Edge()
            self.canvas.get_display().Repaint()
            nearest_int_point = self.get_nearest_intersection(origin_point, section_edge, section)
            measurement_edge = BRepBuilderAPI_MakeEdge(origin_point, nearest_int_point).Edge()
            ais = self.canvas.get_display().DisplayShape(measurement_edge)

    @staticmethod
    def get_nearest_intersection(origin_point, edge, section):
        nearest_param = None
        edge_curve = BRepAdaptor_Curve(edge)
        for element_section in section.get_element_section_list():
            for shape_section in element_section.shapes_section:
                for shape in shape_section[0]:
                    exp = TopExp_Explorer(shape, TopAbs_EDGE)
                    while exp.More():
                        shape_edge = topods.Edge(exp.Current())
                        intersection = IntTools_EdgeEdge(edge, shape_edge)
                        intersection.Perform()
                        if intersection.IsDone():
                            commonparts = intersection.CommonParts()
                            for i in range(commonparts.Length()):
                                commonpart = commonparts.Value(i + 1)
                                print commonpart
                                parameter = commonpart.VertexParameter1()
                                if not nearest_param:
                                    nearest_param = parameter
                                else:
                                    if parameter < nearest_param:
                                        nearest_param = parameter
                        exp.Next()
        if nearest_param:
            point = edge_curve.Value(nearest_param)
            return point
        else:
            return None
