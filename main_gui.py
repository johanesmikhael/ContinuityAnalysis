import sys

from continuity_analyzer_ui import Ui_main_gui
from PyQt5 import QtGui, QtCore, QtWidgets
from ifc_viewer_widget import IfcViewerWidget

from ifcopenshell.geom import occ_utils

# from OCC.Utils import Topo
from OCC import V3d
from OCC.gp import gp_Pln, gp_Dir, gp_Vec
from OCC.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCC.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.TopTools import TopTools_ListIteratorOfListOfShape
from OCC.TopTools import TopTools_HSequenceOfShape
from OCC.TopTools import Handle_TopTools_HSequenceOfShape

from OCC.BRepAlgoAPI import BRepAlgoAPI_Section
from OCC.ShapeAnalysis import ShapeAnalysis_FreeBounds

from OCC.TopoDS import topods_Wire


from ifcproducts import *

from ifcmaterials import *

from section_visualization_gui import *

from slice_visualization_gui import *

from material_browser_gui import *

from section_elements import *

from slice_elements import *

from util import Color

from geom import *

from math import pi

from tkinter import Tk
import tkinter.filedialog
from os.path import isfile


class GuiMainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args):
        QtWidgets.QMainWindow.__init__(self, *args)
        self.ui = Ui_main_gui()
        self.ui.setupUi(self)
        self.setWindowTitle("Main GUI")
        self.resize(2048, 1280)
        self.canvas = IfcViewerWidget(self)
        self.setCentralWidget(self.canvas)
        if not sys.platform == "darwin":
            self.menu_bar = self.menuBar()
        else:
            self.menu_bar = QtWidgets.QMenuBar()
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
        self.section_boxes = []
        self.slice_list = []
        self.path_mark_edges = []
        self.elements = []
        self.material_dict = MaterialDict()

        self.section_visualization_win = None
        self.slice_visualization_win = None
        self.material_browser_win = None

        self.section_distance = 0.2
        self.path_elevation = 1.5
        self.section_plane_size = 2.0
        self.max_height_clearance = 2.0
        self.min_horizontal_clearance = 2.15

        self.viewer_bg_color = Color.white

        self.is_show_section = False
        self.is_show_plane = False
        self.is_show_slice = False
        self.is_show_boxes = False
        self.is_show_model = False

        self.filename = None

        self.p_distance_pointer = 0.0
        self.previous_point = None
        self.pointer_edge = None

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
            _action = QtWidgets.QAction(_callable.__name__.replace('_', ' ').lower(), self)
            _action.setMenuRole(QtWidgets.QAction.NoRole)
            self.connect(_action, QtCore.pyqtSignal('triggered()'), _callable)
            self._menus[menu_name].addAction(_action)
        except KeyError:
            raise ValueError("the menu item %s does not exist" % menu_name)

    def add_toolbar(self, toolbar_name):
        _toolbar = self.addToolBar(toolbar_name)
        self._toolbars[toolbar_name] = _toolbar

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
        self.add_toolbar("Section Analysis")
        self.addToolBarBreak()
        self.add_toolbar("Slices Analysis")
        self.add_function_to_toolbar("Main Toolbar", self.export_image)
        self.add_function_to_toolbar("Main Toolbar", self.open_file)
        self.add_function_to_toolbar("Main Toolbar", self.material_browser)
        self.add_function_to_toolbar("Main Toolbar", self.draw_path)
        self.add_function_to_toolbar("Section Analysis", self.generate_section_plane)
        self.add_function_to_toolbar("Section Analysis", self.toggle_plane_view)
        self.add_function_to_toolbar("Section Analysis", self.process_section)
        self.add_function_to_toolbar("Section Analysis", self.toggle_section_view)
        self.add_function_to_toolbar("Section Analysis", self.analyze_section)
        self.add_function_to_toolbar("Main Toolbar", self.top_view)
        self.add_function_to_toolbar("Main Toolbar", self.iso_view)
        self.add_function_to_toolbar("Slices Analysis", self.generate_slice_box)
        self.add_function_to_toolbar("Slices Analysis", self.toggle_boxes_view)
        self.add_function_to_toolbar("Slices Analysis", self.process_slice)
        self.add_function_to_toolbar("Slices Analysis", self.toggle_slice_view)
        self.add_function_to_toolbar("Slices Analysis", self.analyze_slice)
        self.add_function_to_toolbar("Main Toolbar", self.toggle_model_view)

    def draw_path(self):
        if self.ifc_file is None:
            print("no file opened")
            return
        if not self.canvas.is_draw_path():
            self.canvas.set_draw_path_mode(True)
        else:
            print("drawing mode already On")

    def open_file(self):
        root = Tk()
        root.withdraw()
        file_name = tkinter.filedialog.askopenfilename(filetypes=[("IFC files", "*.ifc")])
        root.destroy()
        if isfile(file_name):
            self.filename = file_name
            self.close_file()  # reset the program
            self.elements = []
            self.ifc_file = ifcopenshell.open(str(file_name))
            self.process_file()
            # self.display_ifc_file()
        else:
            print("No file opened")
        self.is_show_model = True
        self.display_elements()

    def export_image(self):
        f = self.canvas.get_display().View.View().GetObject()
        # print f.Export("tetesdrf.svg", Graphic3d_EF_SVG)
        root = Tk()
        root.withdraw()
        root.destroy()
        import datetime
        now = datetime.datetime.now()
        now_str = now.strftime("%Y-%m-%d_%H%M%S")
        print(self.canvas.get_display().View.Dump(now_str+"_export_main.png"))
        pass

    def process_file(self):
        elements = self.ifc_file.by_type("IfcElement")
        for element in elements:
            is_decompose = BuildingElement.check_ifc_is_decompose(element)
            if not is_decompose:
                if element.is_a("IfcSlab"):
                    slab = element_select.create(self, element, None)
                    self.elements.append(slab)
                    pass
                if element.is_a("IfcWall"):
                    wall = element_select.create(self, element, None)
                    self.elements.append(wall)
                    pass
                if element.is_a("IfcColumn"):
                    column = element_select.create(self, element, None)
                    self.elements.append(column)
                    pass
                if element.is_a("IfcBeam"):
                    beam = element_select.create(self, element, None)
                    self.elements.append(beam)
                    pass
                if element.is_a("IfcCovering"):
                    covering = element_select.create(self, element, None)
                    self.elements.append(covering)
                    pass
                if element.is_a("IfcCurtainWall"):
                    curtain_wall = element_select.create(self, element, None)
                    self.elements.append(curtain_wall)
                    pass
                if element.is_a("IfcDoor"):
                    door = element_select.create(self, element, None)
                    self.elements.append(door)
                    pass
                if element.is_a("IfcWindow"):
                    window = element_select.create(self, element, None)
                    self.elements.append(window)
                    pass
                if element.is_a("IfcRailing"):
                    railing = element_select.create(self, element, None)
                    self.elements.append(railing)
                    pass
                if element.is_a("IfcStair"):
                    stair = element_select.create(self, element, None)
                    self.elements.append(stair)
                    pass
                if element.is_a("IfcRamp"):
                    print("RAMP IS NOT IMPLEMENTED YET")
                    pass
                if element.is_a("IfcRoof"):
                    roof = element_select.create(self, element, None)
                    self.elements.append(roof)
                    pass
                if element.is_a("IfcFurnishingElement"):
                    furniture = element_select.create(self, element, None)
                    self.elements.append(furniture)
                    pass
                if element.is_a("IfcFlowTerminal"):
                    flow_terminal = element_select.create(self, element, None)
                    self.elements.append(flow_terminal)
                    pass
                if element.is_a("IfcBuildingElementProxy"):
                    building_element_proxy = element_select.create(self, element, None)
                    self.elements.append(building_element_proxy)
                    pass
        spatial_structure_elements = self.ifc_file.by_type("IfcSpatialStructureElement")
        for spatial_structure_element in spatial_structure_elements:
            if spatial_structure_element.is_a("IfcSite"):
                site = Site(self, spatial_structure_element, None)
                print(site)
                print(site.main_topods_shape)
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
            print("no curve drawn yet")

    def create_section_plane(self, section_distance):
        crv = self.canvas.get_path_curve()[0]
        display = self.canvas.get_display()
        if crv is not None:
            self.is_show_plane = True
            div_crv_param = divide_curve(crv, section_distance)
            self.clear_crv_sections()
            for i in div_crv_param:
                pt = crv.Value(i)
                pt_vec = crv.DN(i, 1)
                pt_sec_plane = gp_Pln(pt, gp_Dir(pt_vec))
                size = self.section_plane_size
                section_face = BRepBuilderAPI_MakeFace(pt_sec_plane, -size, size, -size, size).Face()
                print(section_face)
                section_face_display = display.DisplayShape(section_face, transparency=0.99, color=255)
                print(section_face_display)
                bounding_box = Bnd_Box()
                brepbndlib_Add(section_face, bounding_box)
                self.section_planes.append((i, section_face, section_face_display, pt_sec_plane, bounding_box, pt_vec))
            display.Repaint()
            return True
        else:
            return False

    def generate_slice_box(self):
        slice_box_success = self.create_slice_box()
        if not slice_box_success:
            print("no section plantes to start with")

    def create_slice_box(self):
        if len(self.section_planes) > 0:
            self.is_show_boxes = True
            display = self.canvas.get_display()
            for i in range(0, len(self.section_planes)-1):
                plane = self.section_planes[i]
                vector = plane[5].Normalized().Scaled(self.section_distance)
                section_slice = BRepPrimAPI_MakePrism(plane[1], vector).Shape()
                print(section_slice)
                section_slice_display = display.DisplayShape(section_slice, transparency=0.95, color=100)
                bounding_box = Bnd_Box()
                brepbndlib_Add(section_slice, bounding_box)
                self.section_boxes.append((i, section_slice, section_slice_display, plane[3], bounding_box))
            return True
        else:
            return False

    def generate_plan(self):
        section_plan_success = self.create_plan(self.path_elevation)

    def create_plan(self, plan_elevation):
        pass

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

    def process_section(self):
        if self.section_list:
            return
        self.is_show_section = True
        self.clear_section()
        if sys.version_info[:3] >= (2, 6, 0):
            import multiprocessing as processing
        else:
            import processing
        n_procs = processing.cpu_count()

        if len(self.section_planes) == 0:
            print("No section planes to intersect with")
            return
        path_curve = self.canvas.get_path_curve()[0]
        self.section_list = self.create_section(path_curve, self.section_planes, self.elements)
        display = self.canvas.get_display()
        for section in self.section_list:
            section.display_coloured_wire(display, Color.ais_green)
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
        if not self.section_list:
            print("no section to analyze")
            return
        if not self.section_visualization_win:
            self.section_visualization_win = GuiVisualization(self)
            self.section_visualization_win.canvas.InitDriver()
            self.section_visualization_win.get_init_section()
        if self.section_visualization_win.isVisible():
            self.section_visualization_win.hide()
        else:
            self.section_visualization_win.show()
        pass

    def process_slice(self):
        if self.slice_list:
            return
        self.is_show_slice = True
        self.clear_slice()
        self.slice_list = self.create_slice(self.section_boxes, self.elements)
        display = self.canvas.get_display()
        for slice in self.slice_list:
            pass
            #slice.display_shape(display)
        display.Repaint()
        pass

    def clear_slice(self):
        display = self.canvas.get_display()
        if self.slice_list:
            for slice in self.slice_list:
                slice.clear_display(display)
        self.section_list = []

    @staticmethod
    def create_slice(section_boxes, elements):
        slice_list = []
        i = 0
        for section_box in section_boxes:
            print(i)
            slice = Slice()
            for element in elements:
                element_slice = ElementSlice.create_element_slice(section_box, element)
                if element_slice:
                    slice.add_element_slice(element_slice)
            slice_list.append(slice)
            i += 1
        return slice_list
        pass

    def analyze_slice(self):
        if not self.slice_list:
            print("no slice to analyze")
            return
        if not self.slice_visualization_win:
            self.slice_visualization_win = GuiVisualization(self)
            self.slice_visualization_win.canvas.InitDriver()
            self.slice_visualization_win.get_init_slice()
        if self.slice_visualization_win.isVisible():
            self.slice_visualization_win.hide()
        else:
            self.slice_visualization_win.show()
        pass

    def get_material_dict(self):
        return self.material_dict

    def toggle_model_view(self):
        self.is_show_model = not self.is_show_model
        display = self.canvas.get_display()
        for element in self.elements:
            pass
            element.set_visible(display, self.is_show_model)

    def toggle_section_view(self):
        self.is_show_section = not self.is_show_section
        display = self.canvas.get_display()
        for section in self.section_list:
            section.set_visible(display, self.is_show_section)

    def toggle_plane_view(self):
        display = self.canvas.get_display()
        self.is_show_plane = not self.is_show_plane
        for plane in self.section_planes:
            if self.is_show_plane:
                display.Context.Display(plane[2])
            else:
                display.Context.Erase(plane[2])

    def toggle_slice_view(self):
        self.is_show_slice = not self.is_show_slice
        display = self.canvas.get_display()
        for slice in self.slice_list:
            slice.set_visible(display, self.is_show_slice)

    def toggle_boxes_view(self):
        display = self.canvas.get_display()
        self.is_show_boxes = not self.is_show_boxes
        for box in self.section_boxes:
            if self.is_show_boxes:
                display.Context.Display(box[2])
            else:
                display.Context.Erase(box[2])

    def create_path_annotation(self):
        self.remove_path_marks()
        display = self.canvas.get_display()
        curve = self.canvas.get_path_curve()[0]
        div_crv_param = divide_curve(curve, 1.0)
        path_marks = []
        for n, i in enumerate(div_crv_param):
            pt = curve.Value(i)
            pt_vec = curve.DN(i, 1)
            pt_vec.Normalize()
            pt_vec.Scale(0.1)
            axis = gp_Ax1()
            axis.SetLocation(pt)
            trans_vec_a = pt_vec.Rotated(axis, pi/2)
            trans_vec_b = pt_vec.Rotated(axis, -pi/2)
            pt_a = pt.Translated(trans_vec_a)
            pt_b = pt.Translated(trans_vec_b)
            edge = create_edge_from_two_point(pt_a, pt_b)
            edge_ais = display.DisplayShape(edge)
            trans_vec_text = trans_vec_a.Scaled(1.2)
            pt_text = pt.Translated(trans_vec_text)
            path_mark = (pt_text.X(), pt_text.Y(), pt_text.Z(), str(n))
            path_marks.append(path_mark)
            self.path_mark_edges.append((edge, edge_ais))
        self.canvas._is_draw_path_mark = path_marks
        pass

    def remove_path_marks(self):
        display = self.canvas.get_display()
        for edge in self.path_mark_edges:
            display.Context.Remove(edge[1])
        self.path_mark_edges = []
        self.canvas._is_draw_path_mark = False

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

    def material_browser(self):
        if not self.material_dict:
            print("No material to browse")
            return
        if not self.material_browser_win:
            self.material_browser_win = GuiMaterialBrowser(self)
        if self.material_browser_win.isVisible():
            self.material_browser_win.hide()
        else:
            self.material_browser_win.show()
        pass

    def set_distance_pointer(self, pointer_distance):
        if self.p_distance_pointer != pointer_distance:
            display = self.canvas.get_display()
            curve = self.canvas.get_path_curve()[0]
            first_param = curve.FirstParameter()
            end_param = curve.LastParameter()
            length = curve_length(curve, first_param, end_param)
            if pointer_distance > length:
                pointer_distance = length
            param = first_param + (end_param-first_param) * pointer_distance / length
            pt = curve.Value(param)
            if self.pointer_edge:
                display.Context.Remove(self.pointer_edge[2])
                #just move it
                self.pointer_edge[0].Translate(self.previous_point, pt)
                self.pointer_edge[1].Translate(self.previous_point, pt)
                edge = create_edge_from_two_point(self.pointer_edge[0], self.pointer_edge[1])
                self.pointer_edge[2] = display.DisplayShape(edge)
                self.previous_point = pt
            else:
                pt_vec = curve.DN(param, 1)
                pt_vec.Normalize()
                axis = gp_Ax1()
                axis.SetLocation(pt)
                rotated_ved = pt_vec.Rotated(axis,pi/2)
                cross_vec = pt_vec.Crossed(rotated_ved)
                cross_vec.Scale(self.section_plane_size * 1.5)
                reserved_vec = cross_vec.Reversed()
                pt_start = pt.Translated(reserved_vec)
                pt_end = pt.Translated(cross_vec)
                edge = create_edge_from_two_point(pt_start, pt_end)
                edge_ais = display.DisplayShape(edge)
                self.pointer_edge = [pt_start, pt_end, edge_ais]
                self.previous_point = pt
            self.p_distance_pointer = pointer_distance
            display.Repaint()
        pass


