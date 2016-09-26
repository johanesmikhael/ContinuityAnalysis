import sys

from continuity_analyzer_ui import Ui_main_gui
from PyQt4 import QtGui, QtCore

from ifc_viewer_widget import IfcViewerWidget

from ifcopenshell.geom import occ_utils

# from OCC.Utils import Topo
from OCC import V3d
from OCC.gp import gp_Pln, gp_Dir
from OCC.GeomAdaptor import GeomAdaptor_Curve
from OCC.GCPnts import GCPnts_AbscissaPoint
from OCC.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCC.TopTools import TopTools_ListIteratorOfListOfShape
from OCC.TopTools import TopTools_HSequenceOfShape
from OCC.TopTools import Handle_TopTools_HSequenceOfShape

from OCC.BRepAlgoAPI import BRepAlgoAPI_Section
from OCC.ShapeAnalysis import ShapeAnalysis_FreeBounds

from OCC.TopoDS import topods_Wire

from ifcproducts import *

from ifcmaterials import *

from visualization_gui import *

from section_elements import *

from quantity import Color


class GuiMainWindow(QtGui.QMainWindow):
    def __init__(self, *args):
        QtGui.QMainWindow.__init__(self, *args)
        self.ui = Ui_main_gui()
        self.ui.setupUi(self)
        self.setWindowTitle("Main GUI")
        self.resize(1024, 640)
        self.canvas = IfcViewerWidget(self)
        self.setCentralWidget(self.canvas)
        if not sys.platform == "darwin":
            self.menu_bar = self.menuBar()
        else:
            self.menu_bar = QtGui.QMenuBar()
        self._menus = {}
        self._menu_methods = {}
        self._toolbars = {}
        self._toolbar_methods = {}
        self.setup_toolbar()

        self.ifcopenshell_setting = ifcopenshell.geom.settings()
        self.ifcopenshell_setting.set(self.ifcopenshell_setting.USE_PYTHON_OPENCASCADE, True)
        self.ifc_file = None
        self.section_planes = []
        self.section_list = []
        self.elements = []
        self.material_dict = MaterialDict()

        self.section_visualization_win = None

        self.section_distance = 0.05
        self.path_elevation = 1.2
        self.section_plane_size = 5.0

        self.viewer_bg_color = Color.white

    # noinspection PyBroadException
    def setup_ifcopenshell_viewer(self, _app):
        display = self.canvas.get_display()

        def add_menu(*args, **kwargs):
            self.add_menu(*args, **kwargs)

        def add_function_to_menu(*args, **kwargs):
            self.add_function_to_menu(*args, **kwargs)

        def start_display():
            self.start_display(_app)

        occ_utils.handle = display
        occ_utils.main_loop = start_display
        occ_utils.add_menu = add_menu
        occ_utils.add_function_to_menu = add_function_to_menu

        viewer_handle = occ_utils.handle.GetViewer()
        viewer = viewer_handle.GetObject()
        while True:
            viewer.InitActiveLights()
            try:
                active_light = viewer.ActiveLight()
            except:
                break
            viewer.DelLight(active_light)
            viewer.NextActiveLights()
        for direction in [(1, 2, -3), (-2, -1, 1)]:
            light = V3d.V3d_DirectionalLight(viewer_handle)
            light.SetDirection(*direction)
            viewer.SetLightOn(light.GetHandle())

    def start_display(self, app):
        self.raise_()
        app.exec_()

    def add_menu(self, menu_name):
        _menu = self.menu_bar.addMenu("&" + menu_name)
        self._menus[menu_name] = _menu

    def add_function_to_menu(self, menu_name, _callable):
        assert callable(_callable), "the function supplied is not callable"
        try:
            _action = QtGui.QAction(_callable.__name__.replace('_', ' ').lower(), self)
            _action.setMenuRole(QtGui.QAction.NoRole)
            self.connect(_action, QtCore.SIGNAL('triggered()'), _callable)
            self._menus[menu_name].addAction(_action)
        except KeyError:
            raise ValueError("the menu item %s does not exist" % menu_name)

    def add_toolbar(self, toolbar_name):
        _toolbar = self.addToolBar(toolbar_name)
        self._toolbars[toolbar_name] = _toolbar

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
        self.add_function_to_toolbar("Main Toolbar", self.open_file)
        self.add_function_to_toolbar("Main Toolbar", self.draw_path)
        self.add_function_to_toolbar("Main Toolbar", self.generate_section_plane)
        self.add_function_to_toolbar("Main Toolbar", self.process_section)
        self.add_function_to_toolbar("Main Toolbar", self.analyze_section)

    def draw_path(self):
        if self.ifc_file is None:
            print "no file opened"
            return
        if not self.canvas.is_draw_path():
            self.canvas.set_draw_path_mode(True)
        else:
            print "drawing mode already On"

    def open_file(self):
        from Tkinter import Tk
        import tkFileDialog
        root = Tk()
        root.withdraw()
        file_name = tkFileDialog.askopenfilename(filetypes=[("IFC files", "*.ifc")])
        root.destroy()
        from os.path import isfile
        if isfile(file_name):
            self.close_file()  # reset the program
            self.elements = []
            self.ifc_file = ifcopenshell.open(str(file_name))
            self.process_file()
            # self.display_ifc_file()
        else:
            print "No file opened"
        self.display_elements()

    def process_file(self):
        elements = self.ifc_file.by_type("IfcElement")
        for element in elements:
            is_decompose = BuildingElement.check_ifc_is_decompose(element)
            if not is_decompose:
                if element.is_a("IfcSlab"):
                    slab = element_select.create(self, element)
                    self.elements.append(slab)
                    pass
                if element.is_a("IfcWall"):
                    wall = element_select.create(self, element)
                    self.elements.append(wall)
                    pass
                if element.is_a("IfcColumn"):
                    column = element_select.create(self, element)
                    self.elements.append(column)
                    pass
                if element.is_a("IfcBeam"):
                    beam = element_select.create(self, element)
                    self.elements.append(beam)
                    pass
                if element.is_a("IfcCovering"):
                    covering = element_select.create(self, element)
                    self.elements.append(covering)
                    pass
                if element.is_a("IfcCurtainWall"):
                    curtain_wall = element_select.create(self, element)
                    self.elements.append(curtain_wall)
                    pass
                if element.is_a("IfcDoor"):
                    door = element_select.create(self, element)
                    self.elements.append(door)
                    pass
                if element.is_a("IfcWindow"):
                    window = element_select.create(self, element)
                    self.elements.append(window)
                    pass
                if element.is_a("IfcRailing"):
                    railing = element_select.create(self, element)
                    self.elements.append(railing)
                    pass
                if element.is_a("IfcStair"):
                    stair = element_select.create(self, element)
                    self.elements.append(stair)
                    pass
                if element.is_a("IfcRamp"):
                    print "RAMP IS NOT IMPLEMENTED YET"
                    pass
                if element.is_a("IfcRoof"):
                    roof = element_select.create(self, element)
                    self.elements.append(roof)
                    pass
                if element.is_a("IfcFurnishingElement"):
                    furniture = element_select.create(self, element)
                    self.elements.append(furniture)
                    pass
                if element.is_a("IfcFlowTerminal"):
                    flow_terminal = element_select.create(self, element)
                    self.elements.append(flow_terminal)
                    pass
                if element.is_a("IfcBuildingElementProxy"):
                    building_element_proxy = element_select.create(self, element)
                    self.elements.append(building_element_proxy)
                    pass
        spatial_structure_elements = self.ifc_file.by_type("IfcSpatialStructureElement")
        for spatial_structure_element in spatial_structure_elements:
            if spatial_structure_element.is_a("IfcSite"):
                site = Site(self, spatial_structure_element)
                print site
                print site.main_topods_shape
                self.elements.append(site)

    def close_file(self):
        # clear section plane if exist
        self.clear_crv_sections()
        # clear section path if exist
        self.clear_section_path()
        # clear ifc products
        self.clear_elements()

    def display_elements(self):
        display = self.canvas.get_display()
        for element in self.elements:
            element.display_shape(display)
        display.FitAll()

    def generate_section_plane(self):
        section_success = self.create_section_plane(self.section_distance)
        if not section_success:
            print "no curve drawn yet"

    def create_section_plane(self, section_distance):
        crv = self.canvas.get_path_curve()[0]
        display = self.canvas.get_display()
        if crv is not None:
            div_crv_param = self.divide_curve(crv, section_distance)
            self.clear_crv_sections()
            for i in div_crv_param:
                pt = crv.Value(i)
                pt_vec = crv.DN(i, 1)
                pt_sec_plane = gp_Pln(pt, gp_Dir(pt_vec))
                size = self.section_plane_size
                section_face = BRepBuilderAPI_MakeFace(pt_sec_plane, -size, size, -size, size).Face()
                section_face_display = display.DisplayShape(section_face, transparency=0.99, color=255)
                self.section_planes.append((i, section_face, section_face_display, pt_sec_plane))
            display.Repaint()
            return True
        else:
            return False

    def clear_crv_sections(self):
        display = self.canvas.get_display()
        for section_plane in self.section_planes:
            display.Context.Clear(section_plane[2])
        self.section_planes = []

    def clear_section_path(self):
        self.canvas.clear_path_curve()

    def clear_elements(self):
        display = self.canvas.get_display()
        display.Context.RemoveAll()
        self.elements = []
        self.ifc_file = None

    def clear_materials(self):
        self.material_dict = MaterialDict()

    @staticmethod
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

    def process_section(self):
        self.clear_section()
        if sys.version_info[:3] >= (2, 6, 0):
            import multiprocessing as processing
        else:
            import processing
        n_procs = processing.cpu_count()

        if len(self.section_planes) == 0:
            print "No section planes to intersect with"
            return
        path_curve = self.canvas.get_path_curve()[0]
        self.section_list = self.create_section(path_curve, self.section_planes, self.elements)
        display = self.canvas.get_display()
        for section in self.section_list:
            section.display_wire(display)
        display.Repaint()

    def clear_section(self):
        display = self.canvas.get_display()
        if self.section_list:
            for section in self.section_list:
                section.clear_display(display)
        self.section_list = []

    @staticmethod
    def create_section(path, section_planes, elements):
        section_list = []
        for section_plane in section_planes:
            section = Section()
            for element in elements:
                element_section = ElementSection.create_element_section(section_plane, element)
                if element_section:
                    section.add_element_section(element_section)
            section_list.append(section)
        return section_list

    def analyze_section(self):
        if not self.section_visualization_win:
            self.section_visualization_win = GuiVisualization(self)
            self.section_visualization_win.canvas.InitDriver()
            self.section_visualization_win.get_init_section()
        if self.section_visualization_win.isVisible():
            self.section_visualization_win.hide()
        else:
            self.section_visualization_win.show()
        pass

    def get_material_dict(self):
        return self.material_dict

