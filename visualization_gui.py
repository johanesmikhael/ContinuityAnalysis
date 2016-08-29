from visualization import Ui_section_visualization
from PyQt4 import QtGui, QtCore
from section_visualization_widget import *

from OCC.gp import gp_Pnt, gp_Trsf, gp_Dir, gp_Ax1
from OCC.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.gce import gce_MakeLin
from OCC.Geom import Geom_Line


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

        self.section_list = []
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
        pass

    def get_section(self):
        for section in self.parent.section_list:
            section_copy = []
            for element_section in section:
                element_section_copy = element_section.create_copy()
                section_copy.append(element_section_copy)
            self.section_list.append(section_copy)

    def display_section(self):
        display = self.canvas.get_display()
        for section in self.section_list:
            for element_section in section:
                element_section.display_wire(display)
        display.FitAll()

    def transform_section(self):
        distance = self.parent.section_distance
        section_planes = self.parent.section_planes
        print "EEEEEEEEEA"
        i = 0
        for section in self.section_list:
            section_plane = section_planes[i]
            section_plane_pln = section_plane[3]
            translation = GuiVisualization.get_translation(section_plane_pln, i, distance)
            rotation = GuiVisualization.get_rotation(section_plane_pln, i, distance)
            for element in section:
                GuiVisualization.transform_element(element, translation)
                GuiVisualization.transform_element(element, rotation)
            i += 1

    def display_axis(self):
        gp_pnt_0 = gp_Pnt(0.0, 0.0, 1.0)
        n = len(self.section_list)
        gp_pnt_1 = gp_Pnt(n*self.parent.section_distance, 0.0, 1.0)
        gp_line = gce_MakeLin(gp_pnt_0, gp_pnt_1).Value()
        geom_line = Geom_Line(gp_line)
        ais = self.canvas.get_display().DisplayShape(geom_line)
        self.section_axis = [geom_line, ais]

    @staticmethod
    def get_translation(section_plane_pln, n_section, section_distance):
        gp_axis_0 = section_plane_pln.Axis()
        gp_point_0 = gp_axis_0.Location()
        gp_point_1 = gp_Pnt(n_section * section_distance, 0.0, 1.0)
        gp_trsf = gp_Trsf()
        gp_trsf.SetTranslation(gp_point_0, gp_point_1)
        return gp_trsf

    @staticmethod
    def get_rotation(section_plane_pln, n_section, section_distance):
        gp_axis_0 = section_plane_pln.Axis()
        gp_point_1 = gp_Pnt(n_section * section_distance, 0.0, 1.0)
        gp_dir = gp_Dir()
        gp_axis_1 = gp_Ax1(gp_point_1, gp_dir)
        rotation_angle = gp_axis_0.Angle(gp_axis_1)
        print rotation_angle
        rotation_axis = gp_Ax1()
        rotation_axis.SetLocation(gp_point_1)
        gp_trsf = gp_Trsf()
        gp_dir_0 = gp_axis_0.Direction()
        if gp_dir_0.Y() >= 0: #the set the rotation direction by determine the axis direction in quadran
            gp_trsf.SetRotation(rotation_axis, -rotation_angle)
        else:
            gp_trsf.SetRotation(rotation_axis, rotation_angle)
        return gp_trsf


    @staticmethod
    def transform_element(element, gp_trsf):
        if not element.is_decomposed:
            for shape_section in element.shapes_section:
                new_topods_wires = []
                for topods_wire in shape_section[0]:
                    new_topods_wires.append(BRepBuilderAPI_Transform(topods_wire, gp_trsf).Shape())
                shape_section[0] = new_topods_wires
        else:
            for child in element.children:
                GuiVisualization.transform_element(child, gp_trsf)
        pass

    def get_init_section(self):
        self.get_section()
        self.transform_section()
        self.display_section()
        self.display_axis()
